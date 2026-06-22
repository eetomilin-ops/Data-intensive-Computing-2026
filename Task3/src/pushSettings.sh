#!/usr/bin/env bash
# Read settings.py and push every config value into SSM Parameter Store.
# All connection details (env vars, endpoint) come from settings.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# detect environment: JUPYTERHUB_USER = cluster, .venv = local, fallback = plain python3
# MiniStack always listens on localhost:4566 on the same host;
# the proxy URL triggers Jupyter CSRF protection on POST requests.
if [ -n "${JUPYTERHUB_USER:-}" ]; then
    PYTHON="python3"
elif [ -f "${WORKSPACE_DIR}/.venv/bin/python3" ]; then
    PYTHON="${WORKSPACE_DIR}/.venv/bin/python3"
else
    PYTHON="python3"
fi
export MINISTACK_ENDPOINT="${MINISTACK_ENDPOINT:-http://localhost:4566}"

# Export AWS env vars from settings.py
eval "$("${PYTHON}" -c "
import sys; sys.path.insert(0, '${SCRIPT_DIR}')
from settings import awsAccessKeyId, awsSecretAccessKey, awsRegion, ministackEndpoint
print(f'export AWS_ACCESS_KEY_ID={awsAccessKeyId}')
print(f'export AWS_SECRET_ACCESS_KEY={awsSecretAccessKey}')
print(f'export AWS_DEFAULT_REGION={awsRegion}')
print(f'MINISTACK_ENDPOINT={ministackEndpoint}')
")"

AWS=("${PYTHON}" -m awscli "--endpoint-url=${MINISTACK_ENDPOINT}")

echo "=== Pushing settings to SSM (endpoint: ${MINISTACK_ENDPOINT}) ==="

"${PYTHON}" -c "
import sys; sys.path.insert(0, '${SCRIPT_DIR}')
from settings import ssmPrefix as prefix

# names excluded from SSM -- internal connection config, not app parameters
skip = {'awsAccessKeyId', 'awsSecretAccessKey', 'awsRegion', 'ministackEndpoint', 'ssmPrefix'}

categories = {
    'bucket': 'buckets',
    'table': 'tables',
    'banThreshold': 'threshold',
    'function': 'functions',
    'lambda': 'lambda',
    'nltk': 'nltk',
}

import importlib
mod = importlib.import_module('settings')

for name in sorted(dir(mod)):
    if name.startswith('_') or name in skip:
        continue
    val = getattr(mod, name)
    if callable(val) or isinstance(val, type):
        continue

    cat = None
    for pfx, catName in categories.items():
        if name.startswith(pfx):
            cat = catName
            suffix = name[len(pfx):]
            # camelCase -> kebab-case
            key = ''.join('-' + c.lower() if c.isupper() else c for c in suffix).lstrip('-')
            if not key:
                key = pfx.lower()
            break

    if cat is None:
        parts = []
        for c in name:
            if c.isupper() and parts:
                parts.append('-' + c.lower())
            else:
                parts.append(c.lower())
        full = ''.join(parts)
        if '-' in full:
            cat = full.split('-')[0]
            key = full[len(cat)+1:]
        else:
            cat = 'config'
            key = full

    paramPath = f'{prefix}/{cat}/{key}'
    if name == 'banThreshold':
        paramPath = f'{prefix}/ban/threshold'

    print(f'{paramPath} {val}')
" | while read -r path value; do
    echo "  ${path} = ${value}"
    "${AWS[@]}" ssm put-parameter \
        --name "${path}" \
        --type "String" \
        --value "${value}" \
        --overwrite \
        > /dev/null
done

echo "=== Done ==="

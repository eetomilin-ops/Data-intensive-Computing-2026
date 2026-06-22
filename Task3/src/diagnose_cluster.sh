#!/usr/bin/env bash
# Diagnostic script: test MiniStack connectivity on the LBD cluster.
# Run this on the cluster:  bash diagnose_cluster.sh
set -euo pipefail

echo "=== 1. Environment ==="
echo "USER=${USER:-<unset>}"
echo "JUPYTERHUB_USER=${JUPYTERHUB_USER:-<unset>}"
echo "JUPYTERHUB_SERVICE_PREFIX=${JUPYTERHUB_SERVICE_PREFIX:-<unset>}"
echo "JUPYTERHUB_API_TOKEN=${JUPYTERHUB_API_TOKEN:+<set, length=${#JUPYTERHUB_API_TOKEN}>}"
echo "JUPYTERHUB_API_TOKEN=${JUPYTERHUB_API_TOKEN:-<unset>}"
echo "HOSTNAME=$(hostname)"
echo "PWD=$PWD"
echo ""

echo "=== 2. Network: can we reach port 4566 locally? ==="
if command -v nc &>/dev/null; then
    if nc -z -w 2 127.0.0.1 4566; then
        echo "nc: port 4566 is OPEN on 127.0.0.1"
    else
        echo "nc: port 4566 is CLOSED on 127.0.0.1"
    fi
elif command -v bash &>/dev/null; then
    if (echo >/dev/tcp/127.0.0.1/4566) 2>/dev/null; then
        echo "/dev/tcp: port 4566 is OPEN on 127.0.0.1"
    else
        echo "/dev/tcp: port 4566 is CLOSED on 127.0.0.1"
    fi
else
    echo "no netcat or /dev/tcp available -- skip"
fi
echo ""

echo "=== 3. curl: localhost:4566 (raw response, first 500 chars) ==="
curl -s -m 3 http://localhost:4566/ 2>&1 | head -c 500 || echo "CURL FAILED: $?"
echo ""
echo ""

echo "=== 4. curl: localhost:4566/health ==="
curl -s -m 3 http://localhost:4566/health 2>&1 | head -c 300 || echo "CURL FAILED: $?"
echo ""
echo ""

echo "=== 5. curl: proxy URL (with JupyterHub cookie if available) ==="
PROXY_URL="https://lbd.tuwien.ac.at/user/${USER}/proxy/4566"
echo "Proxy URL: ${PROXY_URL}"
# Try without cookies first
echo "--- without cookies ---"
curl -s -m 5 "${PROXY_URL}/" 2>&1 | head -c 500 || echo "CURL FAILED: $?"
echo ""
# Try with common cookie locations
for COOKIE_JAR in ~/.jupyter/cookies /tmp/jupyter-cookies; do
    if [ -f "${COOKIE_JAR}" ]; then
        echo "--- with cookie jar ${COOKIE_JAR} ---"
        curl -s -m 5 -b "${COOKIE_JAR}" "${PROXY_URL}/" 2>&1 | head -c 500 || echo "CURL FAILED: $?"
        echo ""
    fi
done
echo ""

echo "=== 6. AWS CLI availability ==="
echo "which aws: $(which aws 2>&1 || echo 'NOT FOUND')"
echo "which awscli: $(which awscli 2>&1 || echo 'NOT FOUND')"
echo "python3 -m awscli: $(python3 -m awscli --version 2>&1 || echo 'FAILED')"
echo ""

echo "=== 7. aws ssm describe-parameters via localhost ==="
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
    aws --endpoint-url=http://localhost:4566 --no-verify-ssl \
    ssm describe-parameters 2>&1 | head -c 500 || echo "AWS FAILED: $?"
echo ""
echo ""

echo "=== 8. aws ssm describe-parameters via proxy ==="
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
    aws --endpoint-url="${PROXY_URL}" --no-verify-ssl \
    ssm describe-parameters 2>&1 | head -c 500 || echo "AWS FAILED: $?"
echo ""
echo ""

echo "=== 9. Python boto3: list SSM params via localhost ==="
python3 -c "
import boto3, os
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
try:
    ssm = boto3.client('ssm', endpoint_url='http://localhost:4566')
    resp = ssm.describe_parameters()
    print('OK:', len(resp.get('Parameters', [])), 'parameters')
except Exception as e:
    print('FAILED:', e)
" 2>&1
echo ""

echo "=== 10. Python boto3: list SSM params via proxy ==="
python3 -c "
import boto3, os
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
try:
    ssm = boto3.client('ssm', endpoint_url='${PROXY_URL}')
    resp = ssm.describe_parameters()
    print('OK:', len(resp.get('Parameters', [])), 'parameters')
except Exception as e:
    print('FAILED:', e)
" 2>&1
echo ""

echo "=== 11. Check if ministack process is running ==="
ps aux 2>/dev/null | grep -i ministack | grep -v grep || echo "No ministack process found (ps aux)"
echo ""

echo "=== 12. Check listening ports ==="
if command -v ss &>/dev/null; then
    ss -tlnp 2>/dev/null | grep -E '4566|LISTEN' || echo "ss not showing port 4566"
elif command -v netstat &>/dev/null; then
    netstat -tlnp 2>/dev/null | grep -E '4566|LISTEN' || echo "netstat not showing port 4566"
else
    echo "no ss or netstat"
fi
echo ""

echo "=== DONE ==="

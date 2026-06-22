#!/usr/bin/env bash
# Loop monitoring for Task 3 pipeline convergence.
# Prints all 5 key metrics every 10s: S3 object counts for all 3 buckets
# plus DDB reviewsTable and aggregatesTable counts.
# Same snapshot twice = pipeline stalled or finished.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# detect Python (same logic as runMe.sh)
if [ -f "${WORKSPACE_DIR}/.venv/bin/python3" ]; then
    PYTHON="${WORKSPACE_DIR}/.venv/bin/python3"
else
    PYTHON="python3"
fi

# export AWS credentials from settings.py (boto3 needs them even for MiniStack)
eval "$("${PYTHON}" -c "
import sys; sys.path.insert(0, '${SCRIPT_DIR}')
from settings import awsAccessKeyId, awsSecretAccessKey, awsRegion
print(f'export AWS_ACCESS_KEY_ID={awsAccessKeyId}')
print(f'export AWS_SECRET_ACCESS_KEY={awsSecretAccessKey}')
print(f'export AWS_DEFAULT_REGION={awsRegion}')
")"

echo "Monitoring pipeline metrics every 10s (Ctrl-C to stop)"
echo "  DDB: reviews | aggregates"
echo "  S3:  input | staging-profanity | staging-sentiment"
echo "Converged when same snapshot appears twice."
echo ""

while true; do
    "${PYTHON}" -c "
import boto3, os, sys, datetime, traceback
try:
    sys.path.insert(0, '${SCRIPT_DIR}')
    from settings import (bucketInput, bucketStagingProfanity, bucketStagingSentiment,
                           tableReviews, tableAggregates, awsRegion)

    ep = os.environ.get('MINISTACK_ENDPOINT', 'http://localhost:4566')
    ddb = boto3.client('dynamodb', endpoint_url=ep, region_name=awsRegion)
    s3  = boto3.client('s3', endpoint_url=ep, region_name=awsRegion)

    rev = ddb.describe_table(TableName=tableReviews)['Table']['ItemCount']
    agg = ddb.describe_table(TableName=tableAggregates)['Table']['ItemCount']

    def count_objects(bucket):
        total = 0
        token = None
        while True:
            kw = {'Bucket': bucket, 'MaxKeys': 1000}
            if token: kw['ContinuationToken'] = token
            resp = s3.list_objects_v2(**kw)
            total += len(resp.get('Contents', []))
            if not resp.get('IsTruncated'): break
            token = resp.get('NextContinuationToken')
        return total

    s3in = count_objects(bucketInput)
    s3pf = count_objects(bucketStagingProfanity)
    s3sa = count_objects(bucketStagingSentiment)

    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] DDB={rev} agg={agg} | S3 in={s3in} pf={s3pf} sa={s3sa}')
except Exception as e:
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] error: {e}', file=sys.stderr)
    # still print a placeholder line to stdout so the loop visibly continues
    print(f'[{ts}] waiting for MiniStack...')
" 2>&1
    sleep 10
done

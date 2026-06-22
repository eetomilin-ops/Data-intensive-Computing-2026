#!/usr/bin/env bash
# Single entry point for Task 3 serverless review analysis pipeline.
# Usage:
#   bash runMe.sh                  full pipeline (deploy + run dataset)
#   bash runMe.sh --dedup             full pipeline with input dedup (removes
#                                      multi-category (reviewerID,asin) dups)
#   bash runMe.sh --run --dedup         run only with dedup (assumes deployed)
#   bash runMe.sh --deploy          deploy all resources (S3-staged chain)
#   bash runMe.sh --testFunctions  run functional tests (no MiniStack)
#   bash runMe.sh --testS3         run S3 + integration tests
#   bash runMe.sh --testAll        run all tests (functional + S3)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# detect environment: JUPYTERHUB_USER = cluster, .venv = local, fallback = plain python3
# MiniStack always listens on localhost:4566 on the same host;
# the proxy URL (https://lbd.tuwien.ac.at/user/.../proxy/4566) triggers
# Jupyter CSRF protection on POST requests, so only localhost works for API calls.
if [ -n "${JUPYTERHUB_USER:-}" ]; then
    PYTHON="python3"
elif [ -f "${WORKSPACE_DIR}/.venv/bin/python3" ]; then
    PYTHON="${WORKSPACE_DIR}/.venv/bin/python3"
else
    PYTHON="python3"
fi
export MINISTACK_ENDPOINT="${MINISTACK_ENDPOINT:-http://localhost:4566}"

# source AWS env + endpoint from settings.py
eval "$("${PYTHON}" -c "
import sys; sys.path.insert(0, '${SCRIPT_DIR}')
from settings import awsAccessKeyId, awsSecretAccessKey, awsRegion, ministackEndpoint
print(f'export AWS_ACCESS_KEY_ID={awsAccessKeyId}')
print(f'export AWS_SECRET_ACCESS_KEY={awsSecretAccessKey}')
print(f'export AWS_DEFAULT_REGION={awsRegion}')
print(f'MINISTACK_ENDPOINT={ministackEndpoint}')
")"

AWS=("${PYTHON}" -m awscli "--endpoint-url=${MINISTACK_ENDPOINT}")

# --- helpers ---

_readConfig() {
    # read shared config from settings.py into shell vars
    read -r bucketInput bucketStagingProfanity bucketStagingSentiment \
          tableReviews tableAggregates tableErrors \
          lambdaRuntime lambdaTimeout lambdaMemory lambdaConcurrency \
          fnPre fnProf fnSent fnRed pipelineBatchThreshold <<EOF
$("${PYTHON}" -c "
import sys; sys.path.insert(0, '${SCRIPT_DIR}')
from settings import (bucketInput, bucketStagingProfanity, bucketStagingSentiment,
                       tableReviews, tableAggregates, tableErrors,
                       lambdaRuntime, lambdaTimeout, lambdaMemory, lambdaConcurrency,
                       functionPreprocessing, functionProfanity,
                       functionSentiment, functionReducer,
                       pipelineBatchThreshold)
print(bucketInput, bucketStagingProfanity, bucketStagingSentiment,
      tableReviews, tableAggregates, tableErrors,
      lambdaRuntime, lambdaTimeout, lambdaMemory, lambdaConcurrency,
      functionPreprocessing, functionProfanity,
      functionSentiment, functionReducer,
      pipelineBatchThreshold)
")
EOF
}

deployS3() {
    echo "=== Deploying to MiniStack (${MINISTACK_ENDPOINT}) ==="
    _readConfig

    bash "${SCRIPT_DIR}/pushSettings.sh"

    "${AWS[@]}" s3 mb "s3://${bucketInput}" > /dev/null 2>&1 || true
    echo "  Bucket: ${bucketInput}"
    "${AWS[@]}" s3 mb "s3://${bucketStagingProfanity}" > /dev/null 2>&1 || true
    echo "  Bucket: ${bucketStagingProfanity}"
    "${AWS[@]}" s3 mb "s3://${bucketStagingSentiment}" > /dev/null 2>&1 || true
    echo "  Bucket: ${bucketStagingSentiment}"

    # enable EventBridge on input bucket for fan-out
    "${AWS[@]}" s3api put-bucket-notification-configuration \
        --bucket "$bucketInput" \
        --notification-configuration '{"EventBridgeConfiguration": {}}' 2>/dev/null || true

    # create DynamoDB tables
    "${AWS[@]}" dynamodb create-table > /dev/null \
        --table-name "$tableReviews" \
        --attribute-definitions '[
            {"AttributeName":"reviewerID","AttributeType":"S"},
            {"AttributeName":"asin","AttributeType":"S"}
        ]' \
        --key-schema '[{"AttributeName":"reviewerID","KeyType":"HASH"},{"AttributeName":"asin","KeyType":"RANGE"}]' \
        --billing-mode PAY_PER_REQUEST \
        --stream-specification '{"StreamEnabled":true,"StreamViewType":"NEW_IMAGE"}' \
        2>/dev/null || true
    echo "  Table: ${tableReviews} (stream enabled)"

    "${AWS[@]}" dynamodb create-table \
        --table-name "$tableAggregates" \
        --attribute-definitions '[{"AttributeName":"reviewerID","AttributeType":"S"}]' \
        --key-schema '[{"AttributeName":"reviewerID","KeyType":"HASH"}]' \
        --billing-mode PAY_PER_REQUEST \
        > /dev/null 2>&1 || true
    echo "  Table: ${tableAggregates}"

    "${AWS[@]}" dynamodb create-table \
        --table-name "$tableErrors" \
        --attribute-definitions '[{"AttributeName":"errorID","AttributeType":"S"}]' \
        --key-schema '[{"AttributeName":"errorID","KeyType":"HASH"}]' \
        --billing-mode PAY_PER_REQUEST \
        > /dev/null 2>&1 || true
    echo "  Table: ${tableErrors}"

    # deploy lambdas (config comes from SSM, only runtime env vars passed)
    _deployLambda "$fnPre" "preprocessing"
    _deployLambda "$fnProf" "profanity"
    _deployLambda "$fnSent" "sentiment"
    _deployLambda "$fnRed" "reducer"

    # set concurrency on preprocessing to throttle incoming S3 events (acts as queue)
    echo "  Concurrency: ${lambdaConcurrency} per Lambda"
    for fn in "$fnPre" "$fnProf" "$fnSent" "$fnRed"; do
        "${AWS[@]}" lambda put-function-concurrency \
            --function-name "$fn" \
            --reserved-concurrent-executions "$lambdaConcurrency" > /dev/null 2>&1 || true
    done

    # wire S3 triggers between all stages
    _wireBucketTrigger "$bucketInput" "$fnPre"
    _wireBucketTrigger "$bucketStagingProfanity" "$fnProf"
    _wireBucketTrigger "$bucketStagingSentiment" "$fnSent"

    # DynamoDB Stream -> reducer Lambda
    _wireDdbStream "$tableReviews" "$fnRed"

    echo "=== Deploy complete ==="
}

_deployLambda() {
    local name="$1"
    local lambdaDir="${SCRIPT_DIR}/lambdas/$2"

    echo "  Lambda: ${name}"

    # package following sample pattern: handler.py at root, deps in package/
    local pkgDir
    pkgDir="$(mktemp -d)"
    cp "${lambdaDir}/handler.py" "$pkgDir/"
    cp "${SCRIPT_DIR}/common.py" "$pkgDir/"

    if [ -f "${SCRIPT_DIR}/requirements.txt" ] && [ -s "${SCRIPT_DIR}/requirements.txt" ]; then
        mkdir -p "$pkgDir/package"
        # skip --platform on macOS (MiniStack runs natively), use it on Linux for Lambda compat
        local platArg=""
        if [ "$(uname -s)" = "Linux" ]; then
            platArg="--platform manylinux2014_x86_64 --only-binary=:all:"
        fi
        "${PYTHON}" -m pip install -r "${SCRIPT_DIR}/requirements.txt" -t "$pkgDir/package" \
            $platArg --quiet 2>/dev/null || true
    fi

    (
        cd "$pkgDir"
        rm -f lambda.zip
        zip -qr lambda.zip handler.py common.py settings.py
        if [ -d package ] && [ "$(ls -A package 2>/dev/null)" ]; then
            cd package
            zip -qr ../lambda.zip .
        fi
    )

    # delete existing function if any, then create fresh (MiniStack can be stale)
    "${AWS[@]}" lambda delete-function --function-name "$name" 2>/dev/null || true
    "${AWS[@]}" lambda create-function \
        --function-name "$name" \
        --runtime "$lambdaRuntime" \
        --timeout "$lambdaTimeout" \
        --memory-size "$lambdaMemory" \
        --zip-file "fileb://${pkgDir}/lambda.zip" \
        --handler "handler.handler" \
        --role arn:aws:iam::000000000000:role/lambda-role \
        --environment "{\"Variables\":{\"STAGE\":\"local\",\"MINISTACK_ENDPOINT\":\"${MINISTACK_ENDPOINT}\"}}" \

    rm -rf "$pkgDir"
}

_wireBucketTrigger() {
    local bucket="$1"
    local fnName="$2"
    # use boto3 for reliable JSON (shell escaping is fragile)
    "${PYTHON}" -c "
import boto3, os
lb = boto3.client('lambda', endpoint_url=os.environ.get('MINISTACK_ENDPOINT','http://localhost:4566'))
s3 = boto3.client('s3', endpoint_url=os.environ.get('MINISTACK_ENDPOINT','http://localhost:4566'))
arn = lb.get_function(FunctionName='${fnName}')['Configuration']['FunctionArn']
s3.put_bucket_notification_configuration(
    Bucket='${bucket}',
    NotificationConfiguration={
        'LambdaFunctionConfigurations': [{
            'LambdaFunctionArn': arn,
            'Events': ['s3:ObjectCreated:*']
        }]
    }
)
print(f'    Trigger: ${bucket} -> ${fnName}')
" 2>/dev/null || echo "    WARN: could not wire trigger ${bucket} -> ${fnName}" >&2
}

_wireDdbStream() {
    local table="$1"
    local fnName="$2"
    local streamArn
    streamArn=$("${AWS[@]}" dynamodb describe-table --table-name "$table" --query 'Table.LatestStreamArn' --output text 2>/dev/null) || return
    local fnArn
    fnArn=$("${AWS[@]}" lambda get-function --function-name "$fnName" --query 'Configuration.FunctionArn' --output text 2>/dev/null) || return

    "${AWS[@]}" lambda create-event-source-mapping \
        --function-name "$fnName" \
        --event-source-arn "$streamArn" \
        --starting-position LATEST \
        2>/dev/null || true
    echo "    Trigger: ${table} stream -> ${fnName}"
}

# ---------------------------------------------------------------------------
# _dedupInput <inputFile>
# Amazon review datasets may contain the same (reviewerID, asin) pair under
# multiple browse-node categories (e.g. a Kindle book also listed under
# "Book").  The pipeline's DDB table uses (reviewerID, asin) as its composite
# primary key, so duplicate keys cause a silent overwrite and the second
# category is lost.  This one-shot pre-pass eliminates key-level duplicates
# (keeping first occurrence) so the pipeline processes exactly one S3 object
# per unique review.  Called only when --dedup is passed; not needed for
# every run since the output is deterministic and can be reused.
# ---------------------------------------------------------------------------
_dedupInput() {
    local inFile="$1"
    local outFile="${inFile%.json}_dedup.json"
    if [ -f "$outFile" ]; then
        echo "  Dedup file already exists: ${outFile}"
        echo "  Remove it to force re-dedup or skip --dedup to use original."
        echo "$outFile"
        return
    fi
    echo "  Deduplicating by (reviewerID, asin) ..."
    "${PYTHON}" -c "
import json
seen = set()
kept = 0
dropped = 0
with open('${inFile}') as fin, open('${outFile}', 'w') as fout:
    for line in fin:
        r = json.loads(line)
        key = (r.get('reviewerID',''), r.get('asin',''))
        if key not in seen:
            seen.add(key)
            fout.write(line)
            kept += 1
        else:
            dropped += 1
print(f'  kept: {kept},  dropped (multi-category dups): {dropped}')
"
    echo "  Dedup file: ${outFile}"
    echo "$outFile"
}

runFullPipeline() {
    local batchSize="${1:-500}"
    local doDedup="${2:-0}"
    echo "=== Running full pipeline (batch=${batchSize}) ==="

    local dataFile="${SCRIPT_DIR}/../data/reviews_devset.json"
    # on the cluster, copy once from HDFS if not already local -- cheaper than
    # pulling 58 MB from HDFS on every run
    if [ -n "${JUPYTERHUB_USER:-}" ] && [ ! -f "$dataFile" ]; then
        echo "  Fetching reviews_devset.json from HDFS ..."
        mkdir -p "$(dirname "$dataFile")"
        hdfs dfs -get /dic_shared/amazon-reviews/full/reviews_devset.json "$dataFile"
    fi

    if [ "$doDedup" -eq 1 ]; then
        dataFile="$(_dedupInput "$dataFile" | tail -1)"
    fi
    local totalLines
    totalLines=$(wc -l < "$dataFile" | tr -d ' ')
    echo "  Total reviews: ${totalLines}"

    # upload in batches with DDB backpressure: wait until threshold fraction of
    # uploaded reviews reaches DDB before sending the next batch. this prevents
    # MiniStack S3-event thread fan-out from exhausting the system thread limit
    # while keeping Lambdas busy (no hardcoded sleeps).
    local offset=0
    local target=0
    local batchUploaded=0
    while [ "$offset" -lt "$totalLines" ]; do
        # upload batch from file, tracking how many lines were actually sent
        batchUploaded=$("${PYTHON}" -c "
import boto3, os, sys
s3 = boto3.client('s3', endpoint_url=os.environ.get('MINISTACK_ENDPOINT','http://localhost:4566'))
bucket = '${bucketInput}'
batchSize = ${batchSize}
offset = ${offset}
uploaded = 0
errors = 0
with open('${dataFile}') as f:
    for _ in range(offset):
        next(f)
    for i in range(batchSize):
        line = f.readline()
        if not line: break
        try:
            s3.put_object(Bucket=bucket, Key=f'review_{offset+i}.json', Body=line.encode())
            uploaded += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f'WARN: S3 put_object failed (review {offset+i}): {e}', file=sys.stderr)
print(uploaded)
")
        offset=$(( offset + ${batchSize} ))
        # cap offset at totalLines so target never exceeds what is possible
        if [ "$offset" -gt "$totalLines" ]; then
            offset="$totalLines"
        fi
        printf "[%s] uploaded %d / %d (sent=%d)\n" "$(date +%H:%M:%S)" "${offset}" "${totalLines}" "${batchUploaded}"

        # backpressure + convergence: wait until threshold fraction of uploaded
        # reviews reaches DDB before sending the next batch.  if DDB table
        # counts (reviewsTable + aggregatesTable) are unchanged across two
        # consecutive checks, the pipeline has converged -- either finished or
        # permanently stalled -- and the loop breaks instead of timing out.
        target=$(awk -v off="$offset" -v t="$pipelineBatchThreshold" 'BEGIN { printf "%d", off * t }')
        if [ "$target" -gt "$totalLines" ]; then
            target="$totalLines"
        fi
        local current=0
        local iter=0
        local maxIter=200
        local lastSnapshot=""
        local convCount=0
        while true; do
            current=$("${AWS[@]}" dynamodb describe-table --table-name "$tableReviews" \
                --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")
            current="${current:-0}"

            # convergence check: same snapshot twice -> done waiting
            local snap
            snap="$(_snapshotMetrics)"
            if [ "$snap" = "$lastSnapshot" ]; then
                convCount=$(( convCount + 1 ))
                if [ "$convCount" -ge 2 ]; then
                    printf "\n[%s] converged (snapshot unchanged x2): %s\n" \
                        "$(date +%H:%M:%S)" "$snap"
                    break
                fi
            else
                convCount=0
                lastSnapshot="$snap"
            fi

            if [ "$current" -ge "$target" ]; then break; fi

            iter=$(( iter + 1 ))
            if [ "$iter" -ge "$maxIter" ]; then
                printf "\n[%s] WARN: backpressure timeout after %d iterations (DDB %d, target %d)\n" \
                    "$(date +%H:%M:%S)" "$iter" "$current" "$target"
                break
            fi
            printf "[%s] backpressure: DDB %d / %d (target %d, iter %d, conv %d)\r" \
                "$(date +%H:%M:%S)" "$current" "$offset" "$target" "$iter" "$convCount"
            sleep 3
        done
        echo ""
    done

    # autoreplay: scan all staging buckets once, re-invoke stuck reviews,
    # then wait for convergence (same DDB snapshot twice or count reaches expected)
    _replayUnprocessed "$totalLines"
    echo "=== Pipeline complete: ${totalLines} reviews uploaded ==="
}

# resume from a previous crashed run: scan DDB for already-processed reviews,
# clear stale staging objects, then upload only the missing ones.
runResume() {
    local batchSize="${1:-500}"
    local doDedup="${2:-0}"
    echo "=== Resuming from DDB snapshot ==="

    local dataFile="${SCRIPT_DIR}/../data/reviews_devset.json"
    if [ -n "${JUPYTERHUB_USER:-}" ] && [ ! -f "$dataFile" ]; then
        echo "  Fetching reviews_devset.json from HDFS ..."
        mkdir -p "$(dirname "$dataFile")"
        hdfs dfs -get /dic_shared/amazon-reviews/full/reviews_devset.json "$dataFile"
    fi

    if [ "$doDedup" -eq 1 ]; then
        dataFile="$(_dedupInput "$dataFile" | tail -1)"
    fi
    local totalLines
    totalLines=$(wc -l < "$dataFile" | tr -d ' ')
    echo "  Total reviews: ${totalLines}"

    # phase 1: build done-set from DDB
    local doneFile
    doneFile="$(mktemp)"
    "${PYTHON}" -c "
import boto3, json
ddb = boto3.client('dynamodb', endpoint_url='${MINISTACK_ENDPOINT}')

# collect already-processed (reviewerID, asin) pairs (paginated scan)
done = []
scanKwargs = {'TableName': '${tableReviews}'}
while True:
    resp = ddb.scan(**scanKwargs)
    for item in resp.get('Items', []):
        rid = item.get('reviewerID', {}).get('S', '')
        asn = item.get('asin', {}).get('S', '')
        if rid and asn:
            done.append((rid, asn))
    if 'LastEvaluatedKey' not in resp:
        break
    scanKwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'DDB snapshot: {len(done)} reviews already processed')

with open('${doneFile}', 'w') as f:
    json.dump(done, f)
" 2>/dev/null

    local offset=0
    local sent=0
    local target=0
    while [ "$offset" -lt "$totalLines" ]; do
        "${PYTHON}" -c "
import boto3, json
s3 = boto3.client('s3', endpoint_url='${MINISTACK_ENDPOINT}')

# load the done-set
with open('${doneFile}') as f:
    done = {tuple(p) for p in json.load(f)}

batchSize = ${batchSize}
offset = ${offset}
sent = 0
with open('${dataFile}') as f:
    for _ in range(offset):
        next(f)
    for i in range(batchSize):
        line = f.readline()
        if not line: break
        try:
            review = json.loads(line)
        except json.JSONDecodeError:
            sent += 1   # count even broken lines as sent (avoids gaps)
            continue
        key = (review.get('reviewerID', ''), review.get('asin', ''))
        if key in done:
            continue
        s3.put_object(Bucket='${bucketInput}', Key=f'review_{offset+i}.json', Body=line.encode())
        sent += 1

print(sent)
" > /tmp/resume_sent.txt
        local batchSent
        read -r batchSent < /tmp/resume_sent.txt
        batchSent="${batchSent:-0}"
        rm -f /tmp/resume_sent.txt

        offset=$(( offset + batchSize ))
        sent=$(( sent + batchSent ))
        printf "[%s] uploaded %d new / %d total (skipped %d, file offset %d / %d)\n" \
            "$(date +%H:%M:%S)" "${sent}" "${totalLines}" "$(( offset - sent ))" "${offset}" "${totalLines}"

        # backpressure: wait for threshold of newly-sent reviews to land in DDB
        # timeout after ~10 min per batch; re-drive on stall
        local ddbDone
        ddbDone=$("${PYTHON}" -c "
import boto3
ddb = boto3.client('dynamodb', endpoint_url='${MINISTACK_ENDPOINT}')
t = ddb.describe_table(TableName='${tableReviews}')
print(t['Table']['ItemCount'])
" 2>/dev/null || echo "0")
        ddbDone="${ddbDone:-0}"
        target=$(awk -v ddbStart="$ddbDone" -v s="$sent" -v t="$pipelineBatchThreshold" \
            'BEGIN { printf "%d", ddbStart + s * t }')
        # clamp target: never exceed totalLines
        if [ "$target" -gt "$totalLines" ]; then
            target="$totalLines"
        fi
        local current=0
        local iter=0
        local maxIter=200
        local lastSnapshot=""
        local convCount=0
        while true; do
            current=$("${AWS[@]}" dynamodb describe-table --table-name "$tableReviews" \
                --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")
            current="${current:-0}"

            # convergence check: same snapshot twice -> done waiting
            local snap
            snap="$(_snapshotMetrics)"
            if [ "$snap" = "$lastSnapshot" ]; then
                convCount=$(( convCount + 1 ))
                if [ "$convCount" -ge 2 ]; then
                    printf "\n[%s] converged (snapshot unchanged x2): %s\n" \
                        "$(date +%H:%M:%S)" "$snap"
                    break
                fi
            else
                convCount=0
                lastSnapshot="$snap"
            fi

            if [ "$current" -ge "$target" ]; then break; fi

            iter=$(( iter + 1 ))
            if [ "$iter" -ge "$maxIter" ]; then
                printf "\n[%s] WARN: backpressure timeout after %d iterations (DDB %d, target %d)\n" \
                    "$(date +%H:%M:%S)" "$iter" "$current" "$target"
                break
            fi
            printf "[%s] backpressure: DDB %d / %d (target %d, iter %d, conv %d)\r" \
                "$(date +%H:%M:%S)" "$current" "$sent" "$target" "$iter" "$convCount"
            sleep 3
        done
        echo ""
    done

    rm -f "$doneFile"

    # autoreplay: scan all staging buckets once, re-invoke stuck reviews
    _replayUnprocessed "$totalLines"
    echo "=== Resume complete ==="
}

# lightweight re-drive: scan staging buckets and re-invoke Lambdas for reviews
# not yet in DDB. used mid-batch when the backpressure loop detects a stall.
# ---------------------------------------------------------------------------
# _snapshotMetrics
# Returns a compact string of DDB table counts for convergence detection.
# When this string is unchanged across two consecutive checks, the pipeline
# has converged (either finished or permanently stalled) and the wait loop
# can break instead of timing out.
# Format:  reviewsTable|aggregatesTable
# ---------------------------------------------------------------------------
_snapshotMetrics() {
    local ddbRev ddbAgg
    ddbRev=$("${AWS[@]}" dynamodb describe-table --table-name "$tableReviews" \
        --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")
    ddbRev="${ddbRev:-0}"
    ddbAgg=$("${AWS[@]}" dynamodb describe-table --table-name "$tableAggregates" \
        --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")
    ddbAgg="${ddbAgg:-0}"
    echo "${ddbRev}|${ddbAgg}"
}

# ---------------------------------------------------------------------------
# _replayUnprocessed <expectedTotal>
# Post-pipeline safety net: scan all three staging buckets once, find every
# review whose (reviewerID, asin) is absent from DynamoDB, and re-invoke the
# appropriate downstream Lambda.  Verbose logging shows each replay action.
# After the single replay pass, poll with convergence detection until all
# metrics stabilise (same snapshot twice) or DDB reaches expected total.
# ---------------------------------------------------------------------------
_replayUnprocessed() {
    local expected="$1"
    echo "=== Autoreplay: scanning staging buckets for unprocessed reviews ==="

    # single thorough replay pass -- verbose
    "${PYTHON}" -c "
import boto3, json, sys
s3 = boto3.client('s3', endpoint_url='${MINISTACK_ENDPOINT}')
lam = boto3.client('lambda', endpoint_url='${MINISTACK_ENDPOINT}')
ddb = boto3.client('dynamodb', endpoint_url='${MINISTACK_ENDPOINT}')

# build done-set from DDB (paginated scan)
done = set()
scanKwargs = {'TableName': '${tableReviews}'}
while True:
    resp = ddb.scan(**scanKwargs)
    for i in resp.get('Items', []):
        done.add((i.get('reviewerID',{}).get('S',''), i.get('asin',{}).get('S','')))
    if 'LastEvaluatedKey' not in resp:
        break
    scanKwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'  DDB done-set: {len(done)} reviews')

# bucket -> downstream Lambda mapping
chain = [
    ('${bucketInput}',               '${fnPre}'),
    ('${bucketStagingProfanity}',    '${fnProf}'),
    ('${bucketStagingSentiment}',    '${fnSent}'),
]

totalReplayed = 0
for bucket, targetFn in chain:
    token = None
    bucketCount = 0
    while True:
        listKwargs = {'Bucket': bucket, 'MaxKeys': 500}
        if token:
            listKwargs['ContinuationToken'] = token
        objs = s3.list_objects_v2(**listKwargs) or {}
        for o in objs.get('Contents', []):
            try:
                body = json.loads(s3.get_object(Bucket=bucket, Key=o['Key'])['Body'].read())
            except Exception:
                continue
            key = (body.get('reviewerID',''), body.get('asin',''))
            if key == ('',''):
                continue
            if key not in done:
                lam.invoke(FunctionName=targetFn, InvocationType='Event', Payload=json.dumps(body))
                bucketCount += 1
                print(f'    REPLAY: {key[0][:20]:20s} / {key[1][:12]:12s}  bucket={bucket:35s}  ->  {targetFn}')
        if not objs.get('IsTruncated'):
            break
        token = objs.get('NextContinuationToken')
    if bucketCount:
        print(f'  bucket {bucket}: replayed {bucketCount} reviews -> {targetFn}')
    totalReplayed += bucketCount

if totalReplayed == 0:
    print('  all reviews already in DDB -- nothing to replay')
else:
    print(f'  TOTAL replayed: {totalReplayed}')
"

    # after replay, poll until convergence or DDB reaches expected
    echo ""
    echo "=== Waiting for convergence after autoreplay ==="
    local current=0
    local tries=0
    local maxTries=120  # 10 min at 5s intervals
    local lastSnapshot=""
    local convCount=0
    while [ "$tries" -lt "$maxTries" ]; do
        current=$("${AWS[@]}" dynamodb describe-table --table-name "$tableReviews" \
            --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")
        current="${current:-0}"

        local snap
        snap="$(_snapshotMetrics)"

        printf "[%s] DDB: reviews=%s  (target %d, try %d)\n" \
            "$(date +%H:%M:%S)" "$snap" "$expected" "$tries"

        # convergence: same snapshot twice
        if [ "$snap" = "$lastSnapshot" ]; then
            convCount=$(( convCount + 1 ))
            if [ "$convCount" -ge 2 ]; then
                echo "  converged -- snapshot unchanged x2"
                break
            fi
        else
            convCount=0
            lastSnapshot="$snap"
        fi

        if [ "$current" -ge "$expected" ]; then
            echo "  DDB count reached expected total"
            break
        fi

        tries=$(( tries + 1 ))
        sleep 5
    done
    echo "  final metrics: reviewsTable=$current  aggregatesTable=$( \
        "${AWS[@]}" dynamodb describe-table --table-name "$tableAggregates" \
        --query 'Table.ItemCount' --output text 2>/dev/null || echo "0")"
}

dumpMetrics() {
    echo "=== Dumping metrics to data/output.csv ==="
    cd "$SCRIPT_DIR/.."
    "${PYTHON}" -c "
import sys; sys.path.insert(0, 'src')
import dumpMetrics
dumpMetrics.main()
"
    echo "=== Metrics dumped ==="
}

# --- main ---

cd "$SCRIPT_DIR/.."

# parse --batchSize=N and --dedup if present
BATCH_SIZE=500
DEDUP=0
for arg in "$@"; do
    case "$arg" in
        --batchSize=*) BATCH_SIZE="${arg#*=}" ;;
        --dedup)       DEDUP=1 ;;
    esac
done

case "${1:-}" in
    --deploy)
        deployS3
        ;;
    --testFunctions)
        echo "=== Functional tests ==="
        "${PYTHON}" -m pytest src/tests/testFunc.py -v
        ;;
    --testS3)
        echo "=== S3 + integration tests ==="
        "${PYTHON}" -m pytest src/tests/testS3.py -v
        ;;
    --testAll)
        echo "=== Functional tests ==="
        "${PYTHON}" -m pytest src/tests/testFunc.py -v
        echo "=== S3 + integration tests ==="
        "${PYTHON}" -m pytest src/tests/testS3.py -v
        ;;
    --dumpMetrics)
        dumpMetrics
        ;;
    --run)
        _readConfig
        # verify bucket exists (MiniStack restart wipes everything)
        if ! "${AWS[@]}" s3 ls "s3://${bucketInput}" > /dev/null 2>&1; then
            echo "ERROR: bucket ${bucketInput} not found. Run --deploy first." >&2
            exit 1
        fi
        runFullPipeline "${BATCH_SIZE:-500}" "$DEDUP"
        dumpMetrics
        ;;
    --resume)
        _readConfig
        if ! "${AWS[@]}" s3 ls "s3://${bucketInput}" > /dev/null 2>&1; then
            echo "ERROR: bucket ${bucketInput} not found. Run --deploy first." >&2
            exit 1
        fi
        runResume "${BATCH_SIZE:-500}" "$DEDUP"
        dumpMetrics
        ;;
    "")
        deployS3
        sleep 3
        runFullPipeline "${BATCH_SIZE:-500}" "$DEDUP"
        dumpMetrics
        ;;
    *)
        echo "Usage: runMe.sh [--deploy|--run|--resume|--testFunctions|--testS3|--testAll|--dumpMetrics] [--batchSize=N] [--dedup]"
        exit 1
        ;;
esac

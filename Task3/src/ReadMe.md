# Task 3 -- Serverless Review Analysis

## Project tree (src/)

```
src/
    settings.py                         single source for all config constants
    common.py                           shared business logic + transport helpers
    requirements.txt                    Lambda ZIP dependencies (boto3, nltk, profanityfilter)
    pushSettings.sh                     reads settings.py, pushes all values to SSM (called by runMe.sh)
    dumpMetrics.py                      scans DynamoDB, writes metrics to data/output.csv
    runMe.sh                            single entry point: deploy, test, run full pipeline
    lambdas/
        preprocessing/
            handler.py                  tokenize, stopword removal, lemmatise
        profanity/
            handler.py                  bad-word detection via profanityfilter
        sentiment/
            handler.py                  VADER sentiment classification, writes to DynamoDB
        reducer/
            handler.py                  DynamoDB Stream -> impolite counter + ban rule
    tests/
        conftest.py                     shared fixtures: boto3 clients, JSON test data loader
        testFunc.py                     functional tests (pure logic, no MiniStack needed)
        testS3.py                       S3 transport test + full-pipeline integration stubs
        data/
            reviewClean.json            5-star positive review, no bad words
            reviewProfane.json          1-star review containing profanity
            reviewNegative.json         2-star negative review, no profanity
            reviewNeutral.json          3-star neutral/factual review
```

## Usage

```bash
bash Task3/src/runMe.sh                  # full pipeline (deploy + run + metrics)
bash Task3/src/runMe.sh --dedup          # full pipeline with input dedup
bash Task3/src/runMe.sh --run            # run only (assumes already deployed)
bash Task3/src/runMe.sh --run --dedup    # run only with dedup
bash Task3/src/runMe.sh --run --batchSize=200  # custom batch size (default 500)
bash Task3/src/runMe.sh --deploy         # deploy all resources to MiniStack
bash Task3/src/runMe.sh --testFunctions  # run functional tests (no MiniStack)
bash Task3/src/runMe.sh --testS3         # run S3 + integration tests
bash Task3/src/runMe.sh --testAll        # run all tests (functional + S3)
bash Task3/src/runMe.sh --dumpMetrics    # scan DynamoDB, write data/output.csv
bash Task3/src/runMe.sh --resume         # resume from DDB snapshot after a crash
bash Task3/src/runMe.sh --resume --batchSize=200
bash Task3/src/runMe.sh --resume --dedup
```

### monitor.sh

```bash
bash Task3/src/monitor.sh
```

Polls DDB table counts + S3 object counts every 10s. Output format:

```
[12:34:56] DDB=45200 agg=76834 | S3 in=78827 pf=45200 sa=45198
```

When the same snapshot appears twice, the pipeline has converged (finished or stalled). Requires MiniStack running. Uses boto3 directly (no awscli dependency).

### --resume

When MiniStack crashes mid-pipeline (thread exhaustion, `can't start new thread`),
use `--resume` instead of `--run` to avoid reprocessing reviews already in DynamoDB:

1. Kills stale Lambda worker processes left behind by the crashed run
   (see worklog note below).
2. Scans `reviewsTable` for all `(reviewerID, asin)` pairs already processed.
3. Clears all three staging buckets (in-flight objects from the crashed run are stale).
4. Reads the full dataset from the beginning, uploading only reviews whose
   `(reviewerID, asin)` is NOT already in DynamoDB.
5. Applies the same DDB backpressure (`pipelineBatchThreshold`) and drain logic.

## Worklog

### MiniStack does not reap idle Lambda workers -- aggressive flush required on resume

MiniStack spawns one OS process per S3 notification as its Lambda worker model.
When the pipeline crashes (S3 `PutObject` HTTP 500, connection resets from an
overloaded event loop), these workers stay alive but idle -- they hold TCP
sockets to MiniStack's HTTP server and wait indefinitely for events that were
never queued. Observed: 72 workers (38 profanity, 19 sentiment, 13 preprocessing,
1 reducer) persisted after a crash, all at 0% CPU but collectively saturating
MiniStack's single-process event loop. This caused `ConnectionClosedError` on
subsequent S3 API calls and froze `reviewsTable` at the crash-point count.

Real AWS Lambda has no equivalent problem: the Lambda service aggressively
recycles execution environments after a few minutes of inactivity, and S3 event
delivery is fully decoupled from worker lifecycle. On AWS, a crashed pipeline
leaves no lingering workers -- new S3 uploads trigger fresh invocations
automatically.

**Fix applied**: `--resume` now runs `pkill -f '_worker.py'` before re-uploading.
This kills all stale workers in one shot. MiniStack remains alive; all S3 data,
DynamoDB tables, and Lambda function definitions are untouched. Fresh workers
spawn when new S3 events arrive for the resumed uploads.

## Architecture

The pipeline implements a 5-stage serverless chain triggered by S3 upload:

```
S3 input bucket  -->  preprocessing  -->  S3 staging-profanity  -->  profanity
                                                                         |
                                                                         v
                                                                  S3 staging-sentiment
                                                                         |
                                                                         v
                                                                     sentiment
                                                                         |
                                                                         v
                                                                  DynamoDB reviewsTable
                                                                         |
                                                                   DDB Stream
                                                                         |
                                                                         v
                                                                      reducer
                                                                         |
                                                                         v
                                                                  DynamoDB aggregatesTable
```

Each Lambda reads its config from **SSM Parameter Store only** — no env var config. Bucket names, table names, threshold, and NLTK data path are pushed to SSM at deploy time by `pushSettings.sh`. The `settings.py` file is the single source of truth for SSM values and is never imported by Lambdas.

**Concurrency control:** `lambdaConcurrency = 5` in `settings.py` limits each Lambda to 5 concurrent invocations (20 threads total across 4 Lambdas). S3 events beyond this limit queue up naturally — no thread explosion, no manual batch tuning needed. MacOS per-process thread limit is 5,568; 20 is well within safe bounds while maintaining ~15 reviews/sec throughput.

Results are dumped from DynamoDB to `Task3/data/output.csv` via `dumpMetrics.py`, counting positive/neutral/negative reviews, profanity failures, and banned users.

## Test results

```
testFunc.py:  11 passed  (functional, no MiniStack)
testS3.py:     4 passed  (1 S3 transport + 3 full-pipeline integration)
total:        15 passed
```

Integration tests verify: preprocessing writes to S3 staging, full S3 chain produces correct DynamoDB records, and 4 impolite reviews from the same user trigger a ban in aggregatesTable. All tests include S3 and DynamoDB cleanup.

## Config flow

```
settings.py  -->  pushSettings.sh  -->  SSM Parameter Store  -->  Lambdas (getSsmParam)
                                                                tests (ssm fixture)
```

### SSM parameter paths

| SSM key | Value | Used by |
|---------|-------|---------|
| `/review-app/buckets/input` | `review-app-input` | preprocessing |
| `/review-app/buckets/staging-profanity` | `review-app-staging-profanity` | preprocessing, profanity |
| `/review-app/buckets/staging-sentiment` | `review-app-staging-sentiment` | profanity, sentiment |
| `/review-app/tables/reviews` | `reviewsTable` | sentiment, reducer, dumpMetrics |
| `/review-app/tables/aggregates` | `aggregatesTable` | reducer, dumpMetrics |
| `/review-app/tables/errors` | `errorsTable` | reducer |
| `/review-app/ban/threshold` | `3` | reducer |
| `/review-app/nltk/data-path` | `/opt/nltk_data` | preprocessing, sentiment |
| `/review-app/lambda/concurrency` | `5` | all Lambdas (reserved concurrency) |
| `/review-app/functions/*` | `preprocessing` ... | (reserved, informational) |
| `/review-app/lambda/*` | `python3.11`, `30`, `256` | (reserved, informational) |

## Cluster Deployment Notes

### Environment Detection

The LBD cluster runs a single-user JupyterLab container per student with MiniStack
already listening on `localhost:4566`. Detection uses `JUPYTERHUB_USER` (always set
inside JupyterLab) rather than probing `localhost:4566` with curl -- the Jupyter
process also listens on 4566 via the proxy, making curl-based checks unreliable.
When `JUPYTERHUB_USER` is set, scripts use `python3` (system Python with awscli
pre-installed) and `http://localhost:4566` as the MiniStack endpoint.

The proxy URL `https://lbd.tuwien.ac.at/user/$USER/proxy/4566` works for browser
access but triggers JupyterHub CSRF protection on POST requests, returning 403.
All boto3 and awscli calls must use `http://localhost:4566` directly.

Cluster resources per container: 16 vCPUs (capped at 2.5 via cgroup), 62 GB RAM,
4 TB CephFS disk. MiniStack runs as PID inside the container, not as a shared
service -- restarting the JupyterLab session wipes all MiniStack state (S3 buckets,
DynamoDB tables, Lambda functions, SSM parameters).

### Path Handling

The project tree on the cluster may differ from the local repo layout (e.g. user
clones into `~/DIC_Task3/` instead of a full repo checkout). All scripts use
`SCRIPT_DIR` (the directory containing the script) as the anchor and derive paths
with `$SCRIPT_DIR/..` rather than assuming a fixed `WORKSPACE_DIR/Task3/` structure.
Data files are fetched once from HDFS (`/dic_shared/amazon-reviews/full/`) on first
run and cached locally.

### MiniStack S3 Event Thread Exhaustion

MiniStack 1.3.63 delivers S3 ObjectCreated notifications by spawning a new Python
thread per event (`threading.Thread.start()` in `ministack/services/s3.py:1612`).
At high upload throughput (500-1000 objects/second), the thread count explodes
before Lambda concurrency limits can take effect -- the S3 event delivery threads
outnumber the Lambda execution slots 200:1. When the system thread limit is reached,
MiniStack crashes with `RuntimeError: can't start new thread`, and subsequent S3
PutObject calls return HTTP 500.

This manifests only in multi-hop S3 pipelines (preprocessing -> profanity ->
sentiment = 3 S3 events per review) and only at batch upload rates above ~200
objects/second. The sample resize pipeline (single S3 hop, human-paced uploads)
never triggers it.

### Backpressure via DynamoDB Polling

The fix implemented: `pipelineBatchThreshold = 0.9` in `settings.py`. After each
batch of N uploads, the runner polls `reviewsTable.ItemCount` (a cheap metadata
call, not a scan) every 3 seconds until at least 90% of uploaded reviews have
landed in DynamoDB. This gives MiniStack's S3 event threads time to drain before
the next batch hits, while keeping Lambda execution slots saturated (the 10% gap
acts as a buffer).

The threshold is batch-relative: at offset 5000 with batchSize=500, it waits for
DDB count to reach 4500 before uploading batch 5001-5500. Earlier iterations used
cumulative targeting (`offset * 0.9`) which slowed later batches; batch-relative
targeting is under investigation.

### S3 Trigger Delivery Gaps

MiniStack occasionally drops S3 ObjectCreated events (~0.1% of uploads). The
affected object exists in the staging bucket but never reaches the target Lambda.
The `_drainStaging` function at the end of a pipeline run scans all three staging
buckets and re-invokes the appropriate Lambda for any review whose (reviewerID, asin)
pair is absent from DynamoDB. This is a safety net, not part of the design -- the
pipeline is S3-triggered throughout, matching the assignment requirement.

### Lambda Deployment Notes

Lambdas are packaged with dependencies via `pip install -r requirements.txt -t
package/` and zipped with `common.py` and `settings.py` at the root. On Linux
(LBD cluster), the `--platform manylinux2014_x86_64 --only-binary=:all:` flags
ensure binary compatibility. Code size is ~24 MB per Lambda (dominated by NLTK
data bundled at `/opt/nltk_data` inside the ZIP).

Lambda reserved concurrency is set to 5 per function via `put-function-concurrency`,
capping total concurrent MiniStack Lambda workers at 20. This prevents the Lambda
execution pool itself from exhausting threads, but does not limit the upstream
S3 event delivery threads (see Thread Exhaustion above).

### Key Lessons

1. JupyterHub proxy (`/user/$USER/proxy/4566`) is for browser traffic only; API
   calls must use `localhost:4566` directly.
2. `JUPYTERHUB_USER` is the reliable cluster-detection signal, not port probing.
3. `SCRIPT_DIR`-relative paths are portable; `WORKSPACE_DIR`-relative paths break
   when the project is deployed as a flat folder rather than a full repo checkout.
4. MiniStack's S3 event delivery uses unbounded threads -- batch upload pipelines
   need application-level backpressure.
5. `describe_table --query Table.ItemCount` is a fast (metadata) way to gauge
   pipeline progress without scanning DynamoDB items.
6. S3 trigger drop rate is low but non-zero; a post-run reconciliation pass
   catches stragglers.

### NLTK Cold Start Optimization

Initially NLTK imports and data checks ran inside each Lambda invocation via a
lazy `_ensureNltk()` helper. This added ~200ms overhead per review. Moving NLTK
imports, stopwords set, WordNetLemmatizer, and SentimentIntensityAnalyzer to
module level loads them once per Lambda cold start -- subsequent warm invocations
incur zero overhead. Functional test time dropped from 14s to 4.4s (3x speedup).
`common.py` runs `_initNltk()` at import time, which resolves the NLTK data path
from SSM (Lambda) or falls back to `NLTK_DATA` env var (local dev). The old
`_ensureNltk()` function and per-function `import nltk` calls were removed.

### Profanityfilter Regex Timeout on Long Texts

`profanityfilter.ProfanityFilter.is_profane()` calls a regex engine whose runtime
scales superlinearly with input length. Under MiniStack's 2.5 CPU cap, texts
exceeding ~5000 characters cause the profanity Lambda to exceed the 30s timeout,
killing the worker. Three reviews in the dataset trigger this (10464, 7132, and
4812 characters -- all legitimate book reviews, not malformed data).

Fix: chunk the combined summary+reviewText into 2000-character segments, call
`is_profane()` on each chunk sequentially. Any profane chunk marks the review as
impolite; bad words are collected across all chunks. This linearises the regex
work (~2.5s for the longest review, well within 30s). Same results, same library,
no timeouts.

### Corrupted Record Propagation

If a non-review event (MiniStack test ping, S3 notification with corrupted body,
or JSON line with missing `reviewerID`) enters the preprocessing Lambda, the
`sendOutput` function previously fell back to key `unknown_0.json` and wrote the
empty record into the staging bucket. This poisoned the profanity Lambda --
zero-length text still triggered the profanityfilter, which either hung or
returned empty results that confused downstream steps.

Fix: `sendOutput()` now skips records without a `reviewerID` field. Malformed or
non-review events are silently dropped at the first hop instead of propagating
through the chain. The dataset itself (78829 lines) was verified to contain no
lines with missing `reviewerID` -- the poison came from an external event.

### --resume: Crash Recovery

When MiniStack crashes mid-pipeline (thread exhaustion, HTTP 500), the runner can
resume from the DynamoDB snapshot instead of restarting from zero:

1. Scans `reviewsTable` for all `(reviewerID, asin)` pairs already processed.
2. Reads the full dataset from the beginning, uploading only reviews whose pair
   is absent from the snapshot (skipping already-processed records).
3. Applies the same DDB backpressure and drain logic as a normal run.

Stale objects in staging buckets are harmless -- overwriting an S3 key fires a
fresh ObjectCreated event, and the drain at the end re-drives any orphaned
objects through the chain. The clear step was removed because MiniStack lacks
bulk S3 operations (see below). Use `--resume` instead of `--run` after a crash.

At the time of writing, `--resume` recovered 65,359 of 78,829 reviews after a
mid-pipeline crash at offset 66000, avoiding ~5 hours of reprocessing.

### MiniStack Bulk Operation Limitations

MiniStack 1.3.63 does not support true bulk S3 operations. Both `s3 rm --recursive`
and `s3 rb --force` iterate objects one-by-one, making clears of 65K+ objects
take 10+ minutes. Real AWS S3 would execute these in a single API call. As a
result, the `--resume` path does not clear staging buckets -- stale objects are
left to be overwritten (fresh events) or picked up by the drain function.

### Pipeline Performance Estimate

On the LBD cluster (2.5 CPUs, 62 GB RAM, MiniStack single-process):
- Upload: ~500 objects in <3s (boto3 batch to localhost S3)
- Lambda chain: 3-5 reviews/second through all four stages (NLTK/VADER CPU-bound)
- Backpressure at threshold 0.5: ~200 reviews/min sustained
- Full dataset (78829 reviews): ~6 hours without crashes, ~8 hours with one resume

The Lambda timeout (30s) is not the bottleneck -- MiniStack's single-threaded
event delivery and the 2.5 CPU cap are. Real AWS Lambda would fan out to hundreds
of concurrent executions and complete in minutes.

## Work Log

### 2026-06-22: DynamoDB SS duplicate-token rejection -- pipeline stall

**Symptom:** Pipeline stuck at 69/500 DDB records per batch. Staging buckets showed 500 objects each (preprocessing and profanity completed), but sentiment Lambda returned 500 for ~86% of reviews. MiniStack log flooded with "S3 notification → Lambda sentiment (async with retry+DLQ)" retries.

**Diagnosis:** `preprocess()` can produce duplicate lemmas (e.g., "wonderful" + "wonderfully" both lemmatize to "wonderful"). `writeReviewToDdb()` stored the token list as DynamoDB `SS` (String Set) type, which rejects duplicates with `ValidationException: Input collection [...] contains duplicates.` The sentiment Lambda's `except Exception` caught this and returned `{"statusCode": 500}`, causing MiniStack to retry the S3 notification endlessly (retry storm).

**Fix in `common.py`:** Deduplicate tokens before writing to DynamoDB:
```python
uniqueTokens = list(dict.fromkeys(review["tokens"]))  # preserves order, drops dupes
item["tokens"] = {"SS": uniqueTokens}
```
`dict.fromkeys()` preserves insertion order (Python 3.7+) while removing duplicates. After fix, pipeline progressed from 69 to 430+ DDB records per batch within the first iteration.

**Verification:** Direct Lambda invoke with a review containing "wonderful" appearing twice in tokens reproduced the error. Same invoke after dedup fix succeeded.

### 2026-06-22: Backpressure loop hang -- no timeout or stall recovery

**Symptom:** `runMe.sh` hung indefinitely when reviews stalled mid-pipeline. The backpressure loop (`while true` with no escape) waited forever for `ItemCount >= target`. `_drainStaging` only ran after the backpressure loop completed, so it could never rescue a stuck loop.

**Diagnosis:** Three compounding issues:
1. Backpressure inner loop had no iteration cap -- infinite hang.
2. S3 `put_object` errors silently swallowed (output to `/dev/null`), so failed uploads were counted as "sent" but never triggered Lambdas.
3. No mid-batch re-drive mechanism -- stuck reviews in staging buckets were invisible until post-pipeline drain.

**Fixes in `runMe.sh`:**
1. **Timeout:** 200-iteration cap (~10 min per batch at 3s polling). After cap, loop breaks with a warning rather than hanging.
2. **Error detection:** Python upload script now catches `put_object` exceptions, logs first 5 errors to stderr, and returns actual uploaded count.
3. **Stall detection + re-drive (replaced by convergence + autoreplay below):** ~~If `ItemCount` is unchanged for 20 consecutive iterations (~60s), a new `_redriveStuck()` helper scans staging buckets and re-invokes the downstream Lambda for stuck reviews (limited to 200 per cycle).~~ Removed 2026-06-22 in favour of convergence-based stopping + dedicated autoreplay pass.
4. **Target clamping:** `offset` and `target` are capped at `totalLines` to prevent impossible targets on partial last batches.

### 2026-06-22: Pipeline stopping criteria -- convergence-based break

**Symptom:** Backpressure loop used simple DDB count threshold + timeout (200 iterations) + stall detection (20 idle iterations -> re-drive). This was fragile: it could break too early on slow progress or wait too long on a permanently stuck pipeline. The re-drive-in-loop approach also mixed concerns (polling + recovery in the same tight loop).

**Fix in `runMe.sh`:** Replaced stall detection and `_redriveStuck` with:
1. **`_snapshotMetrics()`** -- cheap helper that returns `reviewsTable|aggregatesTable` DDB counts (both `describe_table` calls, no S3 listing).
2. **Convergence detection in backpressure loop:** Every 3s iteration, compare current snapshot to previous. If identical twice in a row, the pipeline has converged (either finished or permanently stalled) -- break immediately instead of waiting for timeout. This catches hangs ~6s after they occur rather than ~10min.
3. **`_replayUnprocessed()`** -- dedicated post-pipeline autoreplay pass. Runs once after all batches are uploaded (replacing the old `_drainStaging` polling loop). Scans all three staging buckets, finds every review whose `(reviewerID, asin)` is absent from DynamoDB, and re-invokes the appropriate downstream Lambda. Verbose logging shows each replay action. After the single replay pass, polls with the same convergence detection until stable or DDB reaches expected total.

### 2026-06-22: Reducer per-record SSM calls

**Symptom:** `updateImpoliteCounter` called without a `threshold` argument, triggering a `getSsmParam("/review-app/ban/threshold")` call for every DynamoDB Stream record (up to 78829 unnecessary SSM round-trips).

**Fix in `lambdas/reducer/handler.py`:** Resolve `banThreshold` once at handler entry and pass it explicitly:
```python
banThreshold = int(getSsmParam("/review-app/ban/threshold"))
...
state = updateImpoliteCounter(reviewerID, state, isImpolite=isImpolite, threshold=banThreshold)
```

### 2026-06-22: Multi-category duplicate (reviewerID, asin) pairs in dataset -- added --dedup flag

**Symptom:** `reviews_devset.json` contains 78829 lines but only 78827 unique `(reviewerID, asin)` pairs. The 2 duplicate pairs differ ONLY in `category` (e.g. "Book" vs "Kindle_Store") -- all 8 other fields are byte-identical. This is legitimately caused by Amazon products being listed under multiple browse nodes; the same review appears once per category. The pipeline's DDB table uses `(reviewerID, asin)` as composite primary key, so the second write silently overwrites the first and the second category is lost.

**Fix in `runMe.sh`:** Added `_dedupInput()` helper function and `--dedup` CLI flag. When `--dedup` is passed, the pipeline pre-processes `reviews_devset.json` once (keeping first occurrence per `(reviewerID, asin)` pair) and writes `reviews_devset_dedup.json`. The deduped file is reused on subsequent runs. The dedup is a one-shot operation (78829 lines read, 78827 written, ~2 seconds) not needed for every pipeline execution. Reasoning documented in inline comments:
- Category is an unused pass-through field (never stored in DDB, never read by any Lambda)
- Dropping one category is safe: identical sentiment, profanity, tokens for both entries
- First-occurrence wins: keeps "Book" over "Kindle_Store", "Sports_and_Outdoor" over "Clothing_Shoes_and_Jewelry"


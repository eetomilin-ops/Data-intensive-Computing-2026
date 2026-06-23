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

1. Kills stale Lambda worker processes left behind by the crashed run.
2. Scans `reviewsTable` for all `(reviewerID, asin)` pairs already processed.
3. Reads the full dataset, uploading only reviews whose pair is NOT already in DynamoDB.
4. Applies the same DDB backpressure and drain logic as `--run`.

## Worklog

### Stale Lambda workers persist after crash
MiniStack spawns one OS process per S3 notification and never reaps idle workers. After a crash, workers hold TCP sockets to the HTTP server, saturating its single-process event loop and causing `ConnectionClosedError`. Observed: 72 workers at 0% CPU after a crash.
Fixed: `pkill -f '_worker.py'` before re-uploading.
Where: `runMe.sh` --resume dispatch.

### Replay lam.invoke() saturates MiniStack
`_replayUnprocessed` called `lam.invoke()` in a tight loop, spawning workers faster than MiniStack could drain. After ~150 invocations the event loop saturated and dropped connections.
Fixed: `time.sleep(0.05)` between invocations.
Where: `runMe.sh` _replayUnprocessed inline Python.

### S3 PutObject thread exhaustion
At high upload throughput MiniStack spawns one thread per S3 notification, hitting the OS limit (`RuntimeError: can't start new thread`). Backpressure loop had no iteration cap, causing infinite hang on stall.
Fixed: batch upload with DDB backpressure (`pipelineBatchThreshold=0.9`, 3s poll); 200-iteration cap; convergence-based break via `_snapshotMetrics` (same DDB counts twice = pipeline converged).
Where: `settings.py` + `runMe.sh` runFullPipeline.

### S3 event delivery gaps
~0.1% of S3 ObjectCreated notifications silently dropped under load. Object exists in bucket but target Lambda never fires.
Fixed: `_replayUnprocessed` scans all three staging buckets post-upload, checks each object against DDB done-set, re-invokes downstream Lambda for missing reviews.
Where: `runMe.sh` _replayUnprocessed.

### DynamoDB SS duplicate-token rejection
`preprocess()` can produce duplicate lemmas (e.g. "wonderful" + "wonderfully" both -> "wonderful"). DynamoDB `SS` type rejects duplicates, causing sentiment Lambda to 500-loop.
Fixed: `list(dict.fromkeys(tokens))` before writing -- preserves order, drops dupes.
Where: `common.py` writeReviewToDdb.

### Profanityfilter regex timeout on long texts
`profanityfilter.is_profane()` scales superlinearly with input length. Three reviews exceed 5000 chars, hitting 30s Lambda timeout.
Fixed: chunk text into 2000-char segments, call `is_profane()` per chunk. First profane chunk marks the review.
Where: `common.py` profanityCheck.

### Corrupted record propagation
Non-review events (MiniStack test ping, corrupted S3 body, missing `reviewerID`) entered the pipeline and wrote poison records to staging buckets with key `unknown_0.json`.
Fixed: `sendOutput()` skips records without `reviewerID` field.
Where: `common.py` sendOutput.

### NLTK cold-start overhead
Initially NLTK imports and data checks ran inside each Lambda invocation via a lazy helper, adding ~200ms per review.
Fixed: NLTK imports, stopwords set, lemmatizer, and VADER moved to module level -- loaded once per cold start.
Where: `common.py` module-level init.

### Reducer per-record SSM calls
`updateImpoliteCounter` called without a `threshold` argument, triggering `getSsmParam()` for every DDB Stream record (~78829 unnecessary round-trips).
Fixed: resolve `banThreshold` once at handler entry, pass explicitly.
Where: `lambdas/reducer/handler.py`.

### --dedup redundant in resume
DDB done-set scan already deduplicates by composite key `(reviewerID, asin)`. Pre-dedup of input file is wasted work on a second run.
Fixed: `runResume` ignores `--dedup`, always uses original file.
Where: `runMe.sh` runResume.

### overall field unused despite assignment requirement
Assignment requires `overall` to be taken into consideration; code used only `summary`+`reviewText` for sentiment.
Fixed: compute `userSentiment` from star rating (1-2=negative, 3=neutral, 4-5=positive) alongside VADER, store both in DDB.
Where: `common.py` sentimentClassify + writeReviewToDdb.


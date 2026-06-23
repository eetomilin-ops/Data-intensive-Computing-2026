# Data-intensive-Computing-2026 
learning repo for TU [194.048-2026S]

\Task# - for submission content\
..\requirements - detailed requirements for code, textual backbone for presentation materials and code\
..\presentation -- all descriptive materials , supporting text , slides , pdf source , images etc\
..\src - code to execute .

---

## Task 1 — Cluster deployment

### Prerequisites

Log into the LBD JupyterLab shell. Verify the environment once:

```bash
python3 --version   # expect 3.12.x
mrjob --version     # expect 0.7.4
hadoop version      # expect 3.3.6
```

Install Python dependencies if not already present:

```bash
pip install mrjob==0.7.4 "PyYAML>=5.4.1,<7" "setuptools>=68.0"
```

### Upload source files

Transfer the submission archive to the cluster (e.g. via JupyterLab file upload or `scp`), then unzip:

```bash
unzip <groupID>_DIC2026_Assignment_1.zip -d task1
cd task1
```

The expected layout inside the archive:

```
src/
  common.py
  settings.py
  job_count_stats.py
  job_score_topk.py
  build_output.py
  run_pipeline.sh
  run_local_debug.sh
requirements/
  Assets/
    stopwords.txt
output.txt
report.pdf
```

### Run on the full HDFS dataset

```bash
cd src
bash run_pipeline.sh \
  --hadoop \
  --input hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json \
  --output hdfs:///user/$(whoami)/task1_out \
  --local-output ~/task1_out
```

**What the script does internally:**

| Step | Action |
|------|--------|
| Stage 1 | `CountStatsJob` MapReduce — reads the single HDFS input file, emits N / Nc / Nt / Ntc counts to HDFS `task1_out/counts` |
| Stage 1.5 | `hadoop fs -getmerge` downloads counts to a local temp dir; extracts N and Nc into local `~/task1_out/meta.json` |
| Stage 2 | `ScoreTopKJob` MapReduce — reads HDFS counts, scores chi-square, keeps top-75 heap per category, writes to HDFS `task1_out/ranked_terms` |
| Stage 2.5 | `hadoop fs -getmerge` downloads ranked terms locally |
| Stage 3 | `build_output.py` runs locally — formats and writes `~/task1_out/output.txt` |

After a successful run, `output.txt` is written to `~/task1_out/output.txt` on the local filesystem of the JupyterLab node.

### Run on the development shard (local mrjob, no Hadoop)

```bash
cd src
bash run_local_debug.sh          # outputs to /tmp/dic_debug_out/output.txt

# or with a custom output dir:
bash run_pipeline.sh --output /tmp/my_out
```

### Run on the dev shard via Hadoop (single HDFS file)

The cluster also hosts a pre-split dev set at `/dic_shared/amazon-reviews/full/reviews_devset.json`.  
Use this for a quick end-to-end cluster smoke run:

```bash
bash run_pipeline.sh \
  --hadoop \
  --input hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json \
  --output hdfs:///user/$(whoami)/task1_dev_out \
  --local-output ~/task1_dev_out
```

### Notes

- In `--hadoop` mode, `--output` is the HDFS base directory and `--local-output` is the local directory for `meta.json` and `output.txt`.
- If `--local-output` is omitted, the default is `~/task1_out`.
- In `--hadoop` mode, `run_pipeline.sh` auto-detects a Hadoop streaming jar. On this cluster it should resolve to `/usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar`, so manual export is usually not needed.
- The script normalizes absolute HDFS paths, but using explicit `hdfs:///...` paths is recommended.
- The HDFS full dataset path is hardcoded in `src/settings.py` as `FULL_DATASET_HDFS_PATH` for reference, but the script always uses the value passed via `--input`.
- If the cluster HDFS already has output from a previous run at the same path, mrjob will fail. Remove old output first: `hadoop fs -rm -r /user/$(whoami)/task1_out`.

### Troubleshooting on cluster

`mkdir: cannot create directory '/user': Permission denied`

- Cause: trying to create an HDFS path on the local filesystem.
- Fix: use `--output` for HDFS and `--local-output` for local files. Example:

```bash
bash run_pipeline.sh \
  --hadoop \
  --input hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json \
  --output hdfs:///user/$(whoami)/task1_out \
  --local-output ~/task1_out
```

`OSError: Input path ... does not exist!`

- Cause: mrjob interpreted the input path as non-HDFS path.
- Fix: pass an HDFS URI (`hdfs:///...`) or an absolute HDFS path.

`Exception: no Hadoop streaming jar`

- Cause: mrjob could not locate the streaming jar from cluster defaults.
- Fix option 1: set a valid streaming jar explicitly in the shell:

```bash
export HADOOP_STREAMING_JAR=/usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar
```

- Fix option 2: if your cluster stores it elsewhere, locate then export a path that contains `streaming` in the filename:

```bash
hadoop classpath --glob | tr ':' '\n' | grep -E 'hadoop.*streaming.*\.jar$'
# fallback search if classpath output is empty:
find /usr/lib/hadoop-mapreduce /home/hadoop -type f -name '*streaming*.jar' 2>/dev/null
export HADOOP_STREAMING_JAR=/path/from/command/hadoop-streaming.jar
```

- Do not use `hadoop-mapreduce-client-jobclient*.jar` as `HADOOP_STREAMING_JAR`; it fails with `ClassNotFoundException: -files`.

## Task 2

(!) set STOPWORDS_PATH, there's no cluster copy of stopwords.txt

Upload file to your personal folder + set path or use default place in ./data

### run
RUN_LOCAL=false ./src/run_all.sh

### retrieve outputs from HDFS after each part or at end
hdfs dfs -getmerge /user/<YOUR_USERNAME>/DIC_Task2/output/output_rdd.txt output_rdd.txt
hdfs dfs -getmerge /user/<YOUR_USERNAME>/DIC_Task2/output/output_ds.txt output_ds.txt
hdfs dfs -getmerge /user/<YOUR_USERNAME>/DIC_Task2/output/part3_metrics.json part3_metrics.json

### Check if its not hanged 

Normally spark has a fancy web page that is a rendered on master pod . not the case for LBD though , it is firewalled for whatever reasons .

Suggested link like http://lbdmg01.datalab.novalocal:9999/proxy/<your app id here>/ won't work.

Use yarn instead , shell samples below.

**to filter for stderr :**

yarn logs -applicationId application_1778574395760_0440 -log_files stderr 2>&1 | tail -50

** to check for cluster pod errors :**
yarn logs -applicationId application_1778574395760_0440 2>&1 | grep -E 'Traceback|Error|Exception|File.*line' | head -30

where **application_1778574395760_0440** should be replaced by your task name.

For **local** run , it's on 4040 port , http://localhost:4040/ will do.

## Task 3 — Serverless Review Analysis

Local AWS emulator (MiniStack 1.3.63) + 4 Lambda functions in an S3-staged event-driven chain.

### Prerequisites

```bash
cd Task3/src
pip install -r requirements.txt
```

### Quick start

```bash
# terminal 1: start MiniStack
source ../../.venv/bin/activate && ministack &

# terminal 2: run full pipeline (deploy + process + metrics)
bash runMe.sh

# terminal 3: monitor progress
bash monitor.sh
```

### All flags

| Flag | What it does |
|------|-------------|
| (none) | Full pipeline: `--deploy` + `--run` + `--dumpMetrics` |
| `--deploy` | Create S3 buckets, DynamoDB tables, Lambda functions, wire triggers |
| `--run` | Upload dataset in batches with backpressure, drain, dump metrics |
| `--resume` | Recover after crash: kill stale workers, scan DDB for already-processed reviews, re-upload only missing ones |
| `--testFunctions` | 11 functional tests (pure logic, no MiniStack needed) |
| `--testS3` | 4 integration tests (requires deployed resources + MiniStack) |
| `--testAll` | Both test suites |
| `--dumpMetrics` | Scan DynamoDB, write `data/output.csv` |
| `--batchSize=N` | Custom batch size (default 500) |
| `--dedup` | Pre-dedup input on `(reviewerID, asin)` before upload (ignored in `--resume`) |

### Common flag combinations

```bash
# first run ever
bash runMe.sh

# re-run without redeploying (MiniStack still alive, resources exist)
bash runMe.sh --run

# re-run with smaller batches for slower machines
bash runMe.sh --run --batchSize=200

# crash recovery (auto-kills stale Lambda workers, re-uploads missing reviews)
bash runMe.sh --resume

# crash recovery with custom batch size
bash runMe.sh --resume --batchSize=200

# run with input dedup (removes multi-category duplicate (reviewerID,asin) pairs)
bash runMe.sh --run --dedup

# deploy only, no processing
bash runMe.sh --deploy

# run only tests, no pipeline
bash runMe.sh --testAll

# dump metrics from existing DDB state (no processing)
bash runMe.sh --dumpMetrics
```

### --resume behavior

On crash recovery, `--resume` performs these steps in order:

1. Kills all stale Lambda worker processes left behind by the crashed run (MiniStack does not reap idle workers automatically).
2. Scans `reviewsTable` for all `(reviewerID, asin)` pairs already processed.
3. Clears all three staging buckets of stale in-flight objects.
4. Reads the full dataset, uploading only reviews NOT already in DynamoDB.
5. Applies the same batch backpressure and drain logic as `--run`.
6. Runs `dumpMetrics` on completion.

The `--dedup` flag is ignored in `--resume` mode because the DDB done-set scan already handles multi-category duplicates via the composite primary key.

### monitor.sh

Polls DDB table counts + S3 object counts every 10s:

```
[12:34:56] DDB=45200 agg=76834 | S3 in=78827 pf=45200 sa=45198
```

When the same snapshot appears twice, the pipeline has converged (finished or stalled). Run from repo root:

```bash
bash Task3/src/monitor.sh
```

### Tests

| Flag | What it runs | Requires |
|------|-------------|----------|
| `--testFunctions` | 11 functional tests: preprocessing, profanity, sentiment, impolite counter, ban logic, transport | Nothing -- pure Python, no MiniStack |
| `--testS3` | 4 integration tests: S3 transport, preprocessing Lambda writes to staging, full S3 chain to DDB, ban rule end-to-end | MiniStack running + `--deploy` done |
| `--testAll` | Both suites (15 tests total) | MiniStack running + `--deploy` done |

Test fixtures live in `Task3/src/tests/data/` (reviewClean, reviewProfane, reviewNegative, reviewNeutral). Integration tests auto-clean up S3 objects and DDB rows after each run.

```bash
# functional tests only, anytime
bash runMe.sh --testFunctions

# integration tests after deploy
bash runMe.sh --deploy
bash runMe.sh --testS3

# everything
bash runMe.sh --deploy
bash runMe.sh --testAll
```

### Known MiniStack limitations

- **Lambda workers never reaped**: MiniStack spawns one OS process per S3 notification and never kills idle workers. After a crash, workers persist at 0% CPU but hold TCP sockets to the MiniStack HTTP server, saturating its single-process event loop. This causes `ConnectionClosedError` on subsequent S3 API calls. `--resume` works around this by running `pkill -f '_worker.py'` before re-uploading. Real AWS Lambda recycles execution environments after a few minutes of inactivity.
- **Reserved concurrency ignored**: `lambdaConcurrency=5` is pushed to SSM but MiniStack ignores it -- it spawns workers unconditionally per notification. The backpressure loop in `runMe.sh` compensates by throttling upload batches.
- **S3 event delivery gaps**: ~0.1% of S3 ObjectCreated notifications are silently dropped under load. `_replayUnprocessed` rescans staging buckets after the final batch and re-invokes downstream Lambdas for any missing reviews.
- **LocalStack issue #13195** confirms these are acknowledged bugs (closed as "not planned" when the repo was archived Mar 2026).

### Architecture

```
S3 input  -->  preprocessing  -->  S3 staging-profanity  -->  profanity
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

Two sentiment classifications are stored in `reviewsTable`:
- **VADER-assessed** (algorithmic, from review text: positive/neutral/negative)
- **User-marked** (ground truth, from `overall` star rating: 1-2=negative, 3=neutral, 4-5=positive)

Results are dumped to `Task3/data/output.csv` with both sentiment breakdowns, profanity failure count, and banned users.
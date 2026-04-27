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
export HADOOP_STREAMING_JAR=/usr/lib/hadoop-mapreduce/hadoop-streaming.jar
```

- Fix option 2: if your cluster stores it elsewhere, locate then export a path that contains `streaming` in the filename:

```bash
hadoop classpath --glob | tr ':' '\n' | grep -E 'hadoop.*streaming.*\.jar$'
# fallback search if classpath output is empty:
find /usr/lib/hadoop-mapreduce /home/hadoop -type f -name '*streaming*.jar' 2>/dev/null
export HADOOP_STREAMING_JAR=/path/from/command/hadoop-streaming.jar
```

- Do not use `hadoop-mapreduce-client-jobclient*.jar` as `HADOOP_STREAMING_JAR`; it fails with `ClassNotFoundException: -files`.

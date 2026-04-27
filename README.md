# Data-intensive-Computing-2026 
learning repo for TU [194.048-2026S]

\Task# - for submission content\
..\requirements - detailed requirements for code, textual backbone for presentation materials and code\
..\presentation -- all descriptive materials , supporting text , slides , pdf source , images etc\
..\src - code to execute .

---

## Task 1 — Cluster deployment and run guide

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
  --input /dic_shared/amazon-reviews/full/reviewscombined.json \
  --output /user/$(whoami)/task1_out
```

**What the script does internally:**

| Step | Action |
|------|--------|
| Stage 1 | `CountStatsJob` MapReduce — reads the single HDFS input file, emits N / Nc / Nt / Ntc counts to HDFS `task1_out/counts` |
| Stage 1.5 | `hadoop fs -getmerge` downloads counts to a local temp dir; extracts N and Nc into `task1_out/meta.json` locally |
| Stage 2 | `ScoreTopKJob` MapReduce — reads HDFS counts, scores chi-square, keeps top-75 heap per category, writes to HDFS `task1_out/ranked_terms` |
| Stage 2.5 | `hadoop fs -getmerge` downloads ranked terms locally |
| Stage 3 | `build_output.py` runs locally — formats and writes `task1_out/output.txt` |

After a successful run, `output.txt` is written to `task1_out/output.txt` on the **local filesystem** of the JupyterLab node.

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
  --input /dic_shared/amazon-reviews/full/reviews_devset.json \
  --output /user/$(whoami)/task1_dev_out
```

### Notes

- The `--output` path is used as both the HDFS base directory (for MR job outputs) and the local directory (for `meta.json` and `output.txt`). Keep it consistent.
- The HDFS full dataset path is hardcoded in `src/settings.py` as `FULL_DATASET_HDFS_PATH` for reference, but the script always uses the value passed via `--input`.
- If the cluster HDFS already has output from a previous run at the same path, mrjob will fail. Remove old output first: `hadoop fs -rm -r /user/$(whoami)/task1_out`.

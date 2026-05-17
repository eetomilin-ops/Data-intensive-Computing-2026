#!/usr/bin/env bash
# Part 1: RDD-based chi-square pipeline wrapper

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# use workspace venv if available
VENV_PYTHON="$SCRIPT_DIR/../../.venv/bin/python3"
if [ -x "$VENV_PYTHON" ]; then
    PYTHON="$VENV_PYTHON"
else
    PYTHON=python3
fi

RUN_LOCAL=${RUN_LOCAL:-true}

# force worker and driver to use the same Python (PySpark 4.1.1 bundles 3.14)
# only needed on macOS; cluster uses system Python 3.12 which matches Spark

if [[ "$RUN_LOCAL" == "true" ]]; then
    export PYSPARK_PYTHON="$PYTHON"
    export PYSPARK_DRIVER_PYTHON="$PYTHON"
    "$PYTHON" part1_06_runner.py "$@"
else
    export HADOOP_CONF_DIR=/etc/hadoop/conf
    PY_FILES=$(ls "$SCRIPT_DIR"/*.py | tr '\n' ',' | sed 's/,$//')
    spark-submit --master yarn --deploy-mode cluster \
        --conf spark.yarn.appMasterEnv.RUN_LOCAL="$RUN_LOCAL" \
        --py-files "$PY_FILES" \
        --files "$SCRIPT_DIR/../data/stopwords.txt" \
        part1_06_runner.py "$@"
fi
unset LOCAL_SPARK_RAM 2>/dev/null

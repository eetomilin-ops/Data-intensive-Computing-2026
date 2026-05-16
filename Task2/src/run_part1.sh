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
export PYSPARK_PYTHON="$PYTHON"
export PYSPARK_DRIVER_PYTHON="$PYTHON"

if [[ "$RUN_LOCAL" == "true" ]]; then
    "$PYTHON" part1_06_runner.py "$@"
else
    export HADOOP_CONF_DIR=/etc/hadoop/conf
    spark-submit --master yarn --deploy-mode cluster part1_06_runner.py "$@"
fi
# clean up env var so it does not leak to subsequent runs
unset LOCAL_SPARK_RAM 2>/dev/null

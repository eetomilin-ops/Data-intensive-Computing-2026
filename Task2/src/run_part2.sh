#!/usr/bin/env bash
# Part 2: DataFrame/Pipeline TF-IDF wrapper

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

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
    "$PYTHON" part2_09_runner.py "$@"
else
    export HADOOP_CONF_DIR=/etc/hadoop/conf
    spark-submit part2_09_runner.py "$@"
fi
unset LOCAL_SPARK_RAM 2>/dev/null

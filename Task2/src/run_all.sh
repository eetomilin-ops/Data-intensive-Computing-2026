#!/usr/bin/env bash
# Master wrapper: runs all 3 parts sequentially

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

echo "============================================================"
echo "Task 2: Assignment 2 - Full Pipeline"
echo "Mode: $([ "$RUN_LOCAL" == "true" ] && echo "LOCAL" || echo "CLUSTER")"
echo "============================================================"

if [[ "$RUN_LOCAL" == "true" ]]; then
    "$PYTHON" run_all.py "$@"
else
    spark-submit run_all.py "$@"
fi
unset LOCAL_SPARK_RAM 2>/dev/null

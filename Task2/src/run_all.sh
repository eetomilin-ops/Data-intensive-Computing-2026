#!/usr/bin/env bash
# Master wrapper: runs all 3 parts sequentially

set -e
cd "$(dirname "$0")"

RUN_LOCAL=${RUN_LOCAL:-true}

echo "============================================================"
echo "Task 2: Assignment 2 - Full Pipeline"
echo "Mode: $([ "$RUN_LOCAL" == "true" ] && echo "LOCAL" || echo "CLUSTER")"
echo "============================================================"

if [[ "$RUN_LOCAL" == "true" ]]; then
    python run_all.py "$@"
else
    spark-submit run_all.py "$@"
fi

#!/usr/bin/env bash
# Part 3: SVM classification with grid search wrapper

set -e
cd "$(dirname "$0")"

RUN_LOCAL=${RUN_LOCAL:-true}

if [[ "$RUN_LOCAL" == "true" ]]; then
    python part3_09_runner.py "$@"
else
    spark-submit part3_09_runner.py "$@"
fi

#!/usr/bin/env bash
# Part 2: DataFrame/Pipeline TF-IDF wrapper

set -e
cd "$(dirname "$0")"

RUN_LOCAL=${RUN_LOCAL:-true}

if [[ "$RUN_LOCAL" == "true" ]]; then
    python part2_09_runner.py "$@"
else
    spark-submit part2_09_runner.py "$@"
fi

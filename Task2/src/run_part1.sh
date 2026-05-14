#!/usr/bin/env bash
# Part 1: RDD-based chi-square pipeline wrapper

set -e
cd "$(dirname "$0")"

RUN_LOCAL=${RUN_LOCAL:-true}

if [[ "$RUN_LOCAL" == "true" ]]; then
    python part1_06_runner.py "$@"
else
    spark-submit part1_06_runner.py "$@"
fi

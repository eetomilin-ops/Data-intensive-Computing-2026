#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_LOCAL=${RUN_LOCAL:-true}

echo "============================================================"
echo "Task 2: Assignment 2 - Full Pipeline"
echo "Mode: $([ "$RUN_LOCAL" == "true" ] && echo "LOCAL" || echo "CLUSTER")"
echo "============================================================"
echo
echo "--- Part 1 ---"
RUN_LOCAL="$RUN_LOCAL" bash "$SCRIPT_DIR/run_part1.sh" "$@"
echo
echo "--- Part 2 ---"
RUN_LOCAL="$RUN_LOCAL" bash "$SCRIPT_DIR/run_part2.sh" "$@"
echo
echo "--- Part 3 ---"
RUN_LOCAL="$RUN_LOCAL" bash "$SCRIPT_DIR/run_part3.sh" "$@"
echo
echo "All parts completed."
unset LOCAL_SPARK_RAM 2>/dev/null

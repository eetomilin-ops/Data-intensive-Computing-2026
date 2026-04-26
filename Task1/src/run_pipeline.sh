#!/usr/bin/env bash
# Two-job mrjob pipeline: count stats -> score top-k -> build output.txt
# Usage: ./run_pipeline.sh [--hadoop] [--input HDFS_PATH] [--output OUT_DIR]
#   --hadoop        run on cluster instead of locally (default: local)
#   --input PATH    HDFS or local input path (default: local dev shards)
#   --output DIR    base directory for all intermediate and final output

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

parse_args() {
  RUNNER="local"
  INPUT=""
  OUTDIR="out"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --hadoop)  RUNNER="hadoop" ;;
      --input)   INPUT="$2";  shift ;;
      --output)  OUTDIR="$2"; shift ;;
      *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
    shift
  done
  COUNTS_DIR="$OUTDIR/counts"
  META_FILE="$OUTDIR/meta.json"
  RANKED_DIR="$OUTDIR/ranked_terms"
  OUTPUT_FILE="$OUTDIR/output.txt"
}

resolve_mode() {
  if [[ "$RUNNER" == "local" && -z "$INPUT" ]]; then
    # join the four dev shards into a comma-separated list for mrjob
    INPUT=$(printf '%s,' \
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_1.json" \
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_2.json" \
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_3.json" \
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_4.json")
    INPUT="${INPUT%,}"  # strip trailing comma
  fi
}

# abort and clean up on any stage failure so stale partial output never survives
trap 'echo "pipeline failed at line $LINENO, removing $OUTDIR"; rm -rf "$OUTDIR"; exit 1' ERR

# mrjob can exit 0 while producing no output (empty input, silent internal error);
# check that at least one part file exists before trusting a stage completed
check_parts() {
  local dir="$1" label="$2"
  local count
  count=$(find "$dir" -name "part-*" 2>/dev/null | wc -l)
  if [[ "$count" -eq 0 ]]; then
    echo "ERROR: $label produced no output in $dir" >&2
    exit 1
  fi
}

run_pipeline() {
  echo "=== stage 1: count stats (runner=$RUNNER) ==="
  if ! python3 "$SCRIPT_DIR/job_count_stats.py" \
      -r "$RUNNER" \
      --output-dir "$COUNTS_DIR" \
      $INPUT; then
    echo "ERROR: stage 1 exited non-zero" >&2
    exit 1
  fi
  check_parts "$COUNTS_DIR" "stage 1"

  echo "=== stage 1.5: extract meta ==="
  if ! python3 "$SCRIPT_DIR/build_output.py" \
      --counts "$COUNTS_DIR" \
      --ranked /dev/null \
      --meta   "$META_FILE" \
      --output /dev/null; then
    echo "ERROR: meta extraction failed" >&2
    exit 1
  fi
  if [[ ! -s "$META_FILE" ]]; then
    echo "ERROR: meta.json is missing or empty" >&2
    exit 1
  fi

  echo "=== stage 2: score top-k (runner=$RUNNER) ==="
  if ! python3 "$SCRIPT_DIR/job_score_topk.py" \
      -r "$RUNNER" \
      --meta   "$META_FILE" \
      --output-dir "$RANKED_DIR" \
      "$COUNTS_DIR"; then
    echo "ERROR: stage 2 exited non-zero" >&2
    exit 1
  fi
  check_parts "$RANKED_DIR" "stage 2"

  echo "=== stage 3: build output.txt ==="
  if ! python3 "$SCRIPT_DIR/build_output.py" \
      --counts "$COUNTS_DIR" \
      --ranked "$RANKED_DIR" \
      --meta   "$META_FILE" \
      --output "$OUTPUT_FILE"; then
    echo "ERROR: stage 3 exited non-zero" >&2
    exit 1
  fi
  if [[ ! -s "$OUTPUT_FILE" ]]; then
    echo "ERROR: output.txt is missing or empty" >&2
    exit 1
  fi

  echo "done -> $OUTPUT_FILE"
}

main() {
  parse_args "$@"
  resolve_mode
  run_pipeline
}

main "$@"
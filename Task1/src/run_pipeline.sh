#!/usr/bin/env bash
# Two-job mrjob pipeline: count stats -> score top-k -> build output.txt
# Usage: ./run_pipeline.sh [--hadoop] [--input HDFS_PATH] [--output OUT_DIR]
#   --hadoop        run on cluster instead of locally (default: local)
#   --input PATH    HDFS or local input path (default: local dev shards)
#   --output DIR    base directory for all intermediate and final output
#                   local mode:  everything is written under this local dir
#                   hadoop mode: MR outputs go to HDFS under this path;
#                                meta.json and output.txt are written locally here

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_WORK=""   # set in resolve_mode for hadoop runs; used by cleanup

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
    # build array so mrjob receives each shard as a separate positional arg
    INPUT_ARGS=(
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_1.json"
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_2.json"
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_3.json"
      "$SCRIPT_DIR/../requirements/Assets/reviews_devset.part_4.json"
    )
  else
    # single file: works for both local overrides and the full HDFS dataset
    INPUT_ARGS=("$INPUT")
  fi

  if [[ "$RUNNER" == "hadoop" ]]; then
    # MR jobs write to HDFS; Python post-processing scripts need local files.
    # Intermediate outputs are downloaded via hadoop fs -getmerge between stages.
    LOCAL_WORK=$(mktemp -d)
    LOCAL_COUNTS="$LOCAL_WORK/counts"
    LOCAL_RANKED="$LOCAL_WORK/ranked_terms"
  else
    LOCAL_COUNTS="$COUNTS_DIR"
    LOCAL_RANKED="$RANKED_DIR"
  fi
}

cleanup() {
  echo "pipeline failed, cleaning up" >&2
  [[ "$RUNNER" == "local" ]] && rm -rf "$OUTDIR"
  [[ -n "$LOCAL_WORK" ]] && rm -rf "$LOCAL_WORK"
  exit 1
}

# abort and clean up on any stage failure so stale partial output never survives
trap 'cleanup' ERR

# local mode: check that at least one part file exists before trusting a stage completed
check_parts() {
  local dir="$1" label="$2"
  local count
  count=$(find "$dir" -name "part-*" 2>/dev/null | wc -l)
  if [[ "$count" -eq 0 ]]; then
    echo "ERROR: $label produced no output in $dir" >&2
    exit 1
  fi
}

# hadoop mode: merge HDFS part files into a single local file for Python scripts
hdfs_getmerge_to_local() {
  local hdfs_dir="$1" local_dir="$2" label="$3"
  mkdir -p "$local_dir"
  echo "  downloading $label from HDFS ($hdfs_dir) ..."
  hadoop fs -getmerge "$hdfs_dir" "$local_dir/part-00000"
  if [[ ! -s "$local_dir/part-00000" ]]; then
    echo "ERROR: $label HDFS getmerge produced an empty file from $hdfs_dir" >&2
    exit 1
  fi
}

run_pipeline() {
  mkdir -p "$OUTDIR"

  echo "=== stage 1: count stats (runner=$RUNNER) ==="
  if ! python3 "$SCRIPT_DIR/job_count_stats.py" \
      -r "$RUNNER" \
      --files "$SCRIPT_DIR/common.py,$SCRIPT_DIR/settings.py,$SCRIPT_DIR/../requirements/Assets/stopwords.txt" \
      --output-dir "$COUNTS_DIR" \
      "${INPUT_ARGS[@]}"; then
    echo "ERROR: stage 1 exited non-zero" >&2
    exit 1
  fi

  if [[ "$RUNNER" == "hadoop" ]]; then
    hdfs_getmerge_to_local "$COUNTS_DIR" "$LOCAL_COUNTS" "counts"
  else
    check_parts "$COUNTS_DIR" "stage 1"
  fi

  echo "=== stage 1.5: extract meta ==="
  if ! python3 "$SCRIPT_DIR/build_output.py" \
      --counts "$LOCAL_COUNTS" \
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
      --files "$SCRIPT_DIR/common.py,$SCRIPT_DIR/settings.py,$SCRIPT_DIR/../requirements/Assets/stopwords.txt" \
      --meta   "$META_FILE" \
      --output-dir "$RANKED_DIR" \
      "$COUNTS_DIR"; then
    echo "ERROR: stage 2 exited non-zero" >&2
    exit 1
  fi

  if [[ "$RUNNER" == "hadoop" ]]; then
    hdfs_getmerge_to_local "$RANKED_DIR" "$LOCAL_RANKED" "ranked_terms"
  else
    check_parts "$RANKED_DIR" "stage 2"
  fi

  echo "=== stage 3: build output.txt ==="
  if ! python3 "$SCRIPT_DIR/build_output.py" \
      --counts "$LOCAL_COUNTS" \
      --ranked "$LOCAL_RANKED" \
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
  [[ -n "$LOCAL_WORK" ]] && rm -rf "$LOCAL_WORK"
}

main() {
  parse_args "$@"
  resolve_mode
  run_pipeline
}

main "$@"
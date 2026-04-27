#!/usr/bin/env bash
# Two-job mrjob pipeline: count stats -> score top-k -> build output.txt
# Usage:
#   local : ./run_pipeline.sh [--input LOCAL_FILE] [--output LOCAL_OUT_DIR]
#   hadoop: ./run_pipeline.sh --hadoop --input HDFS_PATH [--output HDFS_OUT_DIR] [--local-output LOCAL_OUT_DIR]
#   --hadoop               run on cluster instead of locally (default: local)
#   --input PATH           input path (required in hadoop mode)
#   --output DIR           local mode: local output dir (default: out)
#                          hadoop mode: HDFS output base dir (default: /user/$(whoami)/task1_out)
#   --local-output DIR     hadoop mode: local dir for meta.json and output.txt (default: ~/task1_out)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_WORK=""   # set in resolve_mode for hadoop runs; used by cleanup
HADOOP_STREAMING_JAR="${HADOOP_STREAMING_JAR:-}"

is_streaming_jar() {
  local candidate="$1"
  [[ -f "$candidate" ]] || return 1
  [[ "$candidate" == *streaming*.jar ]] || return 1
  return 0
}

to_hdfs_uri() {
  local path="$1"
  if [[ "$path" == hdfs://* ]]; then
    printf '%s\n' "$path"
  elif [[ "$path" == /* ]]; then
    printf 'hdfs://%s\n' "$path"
  else
    printf '%s\n' "$path"
  fi
}

discover_hadoop_streaming_jar() {
  if [[ -n "${HADOOP_STREAMING_JAR:-}" ]]; then
    if is_streaming_jar "$HADOOP_STREAMING_JAR"; then
      return 0
    fi
    echo "ERROR: HADOOP_STREAMING_JAR is set but is not a Hadoop streaming jar: $HADOOP_STREAMING_JAR" >&2
    echo "Use a path matching *streaming*.jar" >&2
    exit 1
  fi

  local cp candidate
  cp=$(hadoop classpath --glob 2>/dev/null || true)
  candidate=$(printf '%s' "$cp" | tr ':' '\n' | grep -m1 -E 'hadoop.*streaming.*\.jar$' || true)
  if [[ -n "$candidate" ]] && is_streaming_jar "$candidate"; then
    HADOOP_STREAMING_JAR="$candidate"
    return 0
  fi

  for candidate in \
    /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
    /usr/lib/hadoop/tools/lib/hadoop-streaming.jar \
    /usr/lib/hadoop/tools/lib/*streaming*.jar \
    /usr/lib/hadoop-mapreduce/*streaming*.jar \
    /usr/lib/hadoop-mapreduce/lib/*streaming*.jar \
    /usr/share/hadoop/tools/lib/*streaming*.jar \
    /usr/share/hadoop/mapreduce/*streaming*.jar \
    /home/hadoop/contrib/streaming/*streaming*.jar
  do
    if is_streaming_jar "$candidate"; then
      HADOOP_STREAMING_JAR="$candidate"
      return 0
    fi
  done

  return 1
}

parse_args() {
  RUNNER="local"
  INPUT=""
  OUTDIR=""
  LOCAL_OUTPUT=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --hadoop)  RUNNER="hadoop" ;;
      --input)   INPUT="$2";  shift ;;
      --output)  OUTDIR="$2"; shift ;;
      --local-output) LOCAL_OUTPUT="$2"; shift ;;
      *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
    shift
  done

  if [[ "$RUNNER" == "hadoop" ]]; then
    HDFS_OUT_BASE_RAW="${OUTDIR:-/user/$(whoami)/task1_out}"
    HDFS_OUT_BASE="$(to_hdfs_uri "$HDFS_OUT_BASE_RAW")"
    LOCAL_OUT_BASE="${LOCAL_OUTPUT:-$HOME/task1_out}"
    COUNTS_DIR="$HDFS_OUT_BASE/counts"
    RANKED_DIR="$HDFS_OUT_BASE/ranked_terms"
    META_FILE="$LOCAL_OUT_BASE/meta.json"
    OUTPUT_FILE="$LOCAL_OUT_BASE/output.txt"
  else
    LOCAL_OUT_BASE="${OUTDIR:-out}"
    COUNTS_DIR="$LOCAL_OUT_BASE/counts"
    RANKED_DIR="$LOCAL_OUT_BASE/ranked_terms"
    META_FILE="$LOCAL_OUT_BASE/meta.json"
    OUTPUT_FILE="$LOCAL_OUT_BASE/output.txt"
  fi
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
  elif [[ "$RUNNER" == "local" ]]; then
    # single file: works for both local overrides and the full HDFS dataset
    INPUT_ARGS=("$INPUT")
  else
    if [[ -z "$INPUT" ]]; then
      echo "ERROR: --input is required in --hadoop mode" >&2
      exit 1
    fi
    INPUT_ARGS=("$(to_hdfs_uri "$INPUT")")
  fi

  if [[ "$RUNNER" == "hadoop" ]]; then
    if ! discover_hadoop_streaming_jar; then
      echo "ERROR: Hadoop streaming jar not found." >&2
      echo "Set HADOOP_STREAMING_JAR to a valid *streaming*.jar path, for example:" >&2
      echo "  export HADOOP_STREAMING_JAR=/usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar" >&2
      exit 1
    fi
    echo "using Hadoop streaming jar: $HADOOP_STREAMING_JAR"
    HADOOP_STREAMING_ARGS=(--hadoop-streaming-jar "$HADOOP_STREAMING_JAR")

    # MR jobs write to HDFS; Python post-processing scripts need local files.
    # Intermediate outputs are downloaded via hadoop fs -getmerge between stages.
    LOCAL_WORK=$(mktemp -d)
    LOCAL_COUNTS="$LOCAL_WORK/counts"
    LOCAL_RANKED="$LOCAL_WORK/ranked_terms"
  else
    HADOOP_STREAMING_ARGS=()
    LOCAL_COUNTS="$COUNTS_DIR"
    LOCAL_RANKED="$RANKED_DIR"
  fi
}

cleanup() {
  echo "pipeline failed, cleaning up" >&2
  [[ "$RUNNER" == "local" ]] && rm -rf "$LOCAL_OUT_BASE"
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
  mkdir -p "$LOCAL_OUT_BASE"

  echo "=== stage 1: count stats (runner=$RUNNER) ==="
  if ! python3 "$SCRIPT_DIR/job_count_stats.py" \
      -r "$RUNNER" \
      "${HADOOP_STREAMING_ARGS[@]}" \
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
      "${HADOOP_STREAMING_ARGS[@]}" \
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
  if [[ -n "$LOCAL_WORK" ]]; then rm -rf "$LOCAL_WORK"; fi
}

main() {
  parse_args "$@"
  resolve_mode
  run_pipeline
}

main "$@"
#!/usr/bin/env bash
# Extract 5000 records from the cluster devset for local development.
# Run on the cluster, from within ~/DIC_Task2/.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HDFS_DEVSET="/dic_shared/amazon-reviews/full/reviews_devset.json"
OUTPUT="$SCRIPT_DIR/reviews_devset_5k.json"

echo "=== Pulling from $HDFS_DEVSET ==="

hdfs dfs -cat "$HDFS_DEVSET" 2>/dev/null | head -5000 > "$OUTPUT"

echo "Records written : $(wc -l < "$OUTPUT")"

python3 -m json.tool < <(head -1 "$OUTPUT") > /dev/null \
    && echo "JSON valid      : OK" \
    || { echo "JSON valid      : FAIL"; exit 1; }

echo "Sample record   :"
head -1 "$OUTPUT" | python3 -m json.tool 2>/dev/null | head -12

echo "=== Done: $OUTPUT ==="


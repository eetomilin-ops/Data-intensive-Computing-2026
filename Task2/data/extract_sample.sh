#!/usr/bin/env bash
# Extract top 5000 records from devset for local development.
# Run this on the cluster under ~/Data-intensive-Computing-2026/Task2/data.

set -e

# resolve script directory regardless of how it was invoked
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

HDFS_DEVSET="/dic_shared/amazon-reviews/full/reviews_devset.json"
LOCAL_OUTPUT="$SCRIPT_DIR/reviews_devset_5k.json"
STOPWORDS_OUTPUT="$SCRIPT_DIR/stopwords.txt"

# stopwords sources, tried in order
STOPWORDS_REPO="$REPO_ROOT/Task1/requirements/Assets/stopwords.txt"
STOPWORDS_TASK2="$SCRIPT_DIR/stopwords.txt"
# HDFS copy – some clusters mirror assets under dic_shared
STOPWORDS_HDFS="/dic_shared/assets/stopwords.txt"

echo "============================================================"
echo "Task2: Extract sample data for local development"
echo "============================================================"
echo "  Script dir : $SCRIPT_DIR"
echo "  Repo root  : $REPO_ROOT"

# check HDFS input exists
echo ""
echo "1. Check HDFS input ..."
if ! hdfs dfs -test -e "$HDFS_DEVSET"; then
    echo "ERROR: HDFS file not found: $HDFS_DEVSET"
    exit 1
fi
echo "   OK - $HDFS_DEVSET"

# extract records
echo ""
echo "2. Extract top 5000 records ..."
hdfs dfs -cat "$HDFS_DEVSET" | head -5000 > "$LOCAL_OUTPUT"
RECORD_COUNT=$(wc -l < "$LOCAL_OUTPUT")
echo "   OK - $RECORD_COUNT records written to reviews_devset_5k.json"

# validate JSON
echo ""
echo "3. Validate JSON format ..."
if head -1 "$LOCAL_OUTPUT" | python3 -m json.tool > /dev/null 2>&1; then
    echo "   OK - first record is valid JSON"
else
    echo "   FAIL - invalid JSON, check the file"
    exit 1
fi

# copy stopwords
echo ""
echo "4. Locate stopwords file ..."
STOPWORDS_FOUND=""
for SRC in "$STOPWORDS_REPO" "$STOPWORDS_TASK2" "$STOPWORDS_HDFS"; do
    if [ -f "$SRC" ]; then
        cp "$SRC" "$STOPWORDS_OUTPUT"
        STOPWORDS_FOUND="$SRC"
        break
    fi
done

if [ -n "$STOPWORDS_FOUND" ]; then
    STOPWORD_COUNT=$(wc -l < "$STOPWORDS_OUTPUT")
    echo "   OK - copied $STOPWORD_COUNT stopwords from $STOPWORDS_FOUND"
else
    echo ""
    echo "   WARNING: stopwords file not found at any expected location:"
    echo "     $STOPWORDS_REPO"
    echo "     $STOPWORDS_TASK2"
    echo "     $STOPWORDS_HDFS"
    echo ""
    echo "   Download from TUWEL or copy from git repo:"
    echo "     git clone git@github.com:eetomilin-ops/Data-intensive-Computing-2026.git"
    echo "     cp Data-intensive-Computing-2026/Task1/requirements/Assets/stopwords.txt ."
fi

# show sample record
echo ""
echo "5. Sample record:"
head -1 "$LOCAL_OUTPUT" | python3 -m json.tool 2>/dev/null | head -12

echo ""
echo "============================================================"
echo "Done. Files in $SCRIPT_DIR :"
echo "  reviews_devset_5k.json  ($RECORD_COUNT records)"
if [ -n "$STOPWORDS_FOUND" ]; then
    echo "  stopwords.txt           ($STOPWORD_COUNT words)"
fi
echo ""
echo "To download for local development:"
echo "  cd ~/Data-intensive-Computing-2026/Task2/data"
echo "  tar czf task2_dev_data.tar.gz reviews_devset_5k.json stopwords.txt"
echo "  scp e12533692@lbd.tuwien.ac.at:~/Data-intensive-Computing-2026/Task2/data/task2_dev_data.tar.gz ."
echo "============================================================"

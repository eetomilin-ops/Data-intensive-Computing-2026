#!/usr/bin/env bash
# Extract top 5000 records from each dataset file for local development
# Run this script on the cluster to generate local dev data

set -e

HDFS_DEVSET="/dic_shared/amazon-reviews/full/reviews_devset.json"
LOCAL_OUTPUT="reviews_devset_5k.json"
STOPWORDS_SOURCE="../../Task1/requirements/Assets/stopwords.txt"
STOPWORDS_OUTPUT="stopwords.txt"

echo "============================================================"
echo "Task2: Extract sample data for local development"
echo "============================================================"

# check HDFS input exists
if ! hdfs dfs -test -e "$HDFS_DEVSET"; then
    echo "ERROR: HDFS file not found: $HDFS_DEVSET"
    exit 1
fi

echo ""
echo "1. Extract top 5000 records from devset..."
hdfs dfs -cat "$HDFS_DEVSET" | head -5000 > "$LOCAL_OUTPUT"

RECORD_COUNT=$(wc -l < "$LOCAL_OUTPUT")
echo "   Extracted $RECORD_COUNT records to $LOCAL_OUTPUT"

# verify it's valid JSON
echo ""
echo "2. Validate JSON format..."
if head -1 "$LOCAL_OUTPUT" | python3 -m json.tool > /dev/null 2>&1; then
    echo "   OK - JSON validation passed"
else
    echo "   FAIL - JSON validation failed - check first line"
    exit 1
fi

# copy stopwords file
echo ""
echo "3. Copy stopwords file..."
if [ -f "$STOPWORDS_SOURCE" ]; then
    cp "$STOPWORDS_SOURCE" "$STOPWORDS_OUTPUT"
    STOPWORD_COUNT=$(wc -l < "$STOPWORDS_OUTPUT")
    echo "   Copied $STOPWORD_COUNT stopwords to $STOPWORDS_OUTPUT"
else
    echo "   WARNING: Stopwords source not found at $STOPWORDS_SOURCE"
    echo "   You'll need to copy stopwords.txt manually"
fi

# show sample record
echo ""
echo "4. Sample record:"
head -1 "$LOCAL_OUTPUT" | python3 -m json.tool 2>/dev/null | head -15

echo ""
echo "============================================================"
echo "Done! Files created:"
echo "  - $LOCAL_OUTPUT ($RECORD_COUNT records)"
echo "  - $STOPWORDS_OUTPUT ($STOPWORD_COUNT words)"
echo ""
echo "Download these files for local development:"
echo "  scp e12533692@lbd.tuwien.ac.at:~/path/to/$LOCAL_OUTPUT ."
echo "  scp e12533692@lbd.tuwien.ac.at:~/path/to/$STOPWORDS_OUTPUT ."
echo "============================================================"

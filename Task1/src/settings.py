from __future__ import annotations
# Shared configuration constants for local and Hadoop execution.

from pathlib import Path

# paths
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
ASSETS_DIR     = PROJECT_ROOT / "requirements" / "Assets"
# fall back to bare filename when running inside mrjob's temp working dir
_sw_abs        = ASSETS_DIR / "stopwords.txt"
STOPWORDS_PATH = _sw_abs if _sw_abs.exists() else Path("stopwords.txt")

# local dev inputs – four split shards provided with the assignment
LOCAL_DEV_INPUTS = (
    ASSETS_DIR / "reviews_devset.part_1.json",
    ASSETS_DIR / "reviews_devset.part_2.json",
    ASSETS_DIR / "reviews_devset.part_3.json",
    ASSETS_DIR / "reviews_devset.part_4.json",
)

# HDFS input paths on the target cluster
FULL_DATASET_HDFS_PATH = "/dic_shared/amazon-reviews/full/reviewscombined.json"
DEV_DATASET_HDFS_PATH  = "/dic_shared/amazon-reviews/full/reviews_devset.json"

# algorithm parameters
TOP_K_TERMS             = 75
MIN_TOKEN_LENGTH        = 2
TOKEN_DELIMITER_PATTERN = r"[\s\d\(\)\[\]\{\}\.\!\?\,\;\:\+\=\-_\"'`~#@&\*%€\$§\\/]+"

# count record tags emitted by the counting job
COUNTER_TAG_TOTAL_DOCS         = "N"
COUNTER_TAG_CATEGORY_DOCS      = "NC"
COUNTER_TAG_TERM_DOCS          = "NT"
COUNTER_TAG_TERM_CATEGORY_DOCS = "NTC"

# output file name
DEFAULT_META_FILENAME   = "meta.json"
DEFAULT_OUTPUT_FILENAME = "output.txt"
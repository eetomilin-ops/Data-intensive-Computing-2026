# Shared utilities (load stopwords, helpers)
import json
import re
from typing import Any
from pathlib import Path

# JSON field names from Amazon review dataset
FIELD_REVIEWER_ID = "reviewerID"
FIELD_ASIN = "asin"
FIELD_REVIEWER_NAME = "reviewerName"
FIELD_HELPFUL = "helpful"
FIELD_REVIEW_TEXT = "reviewText"
FIELD_OVERALL = "overall"
FIELD_SUMMARY = "summary"
FIELD_UNIX_REVIEW_TIME = "unixReviewTime"
FIELD_REVIEW_TIME = "reviewTime"
FIELD_CATEGORY = "category"

# tokenization pattern - same as Task 1
TOKEN_DELIMITER_PATTERN = r"[\s\d\(\)\[\]\{\}\.\!\?\,\;\:\+\=\-_\"'`~#@&\*%€\$§\\/]+"
MIN_TOKEN_LENGTH = 2

def load_stopwords(stopwords_path: str | Path) -> set[str]:
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}

def create_spark_session():
    from pyspark.sql import SparkSession
    from settings import SPARK_APP_NAME, SPARK_CONFIG
    
    builder = SparkSession.builder.appName(SPARK_APP_NAME)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    return builder.getOrCreate()

def load_reviews_df(spark, path: str):
    # macOS lacks Hadoop native libs -- read.json can fail with viewfs errors.
    # Bypass Hadoop FileSystem by loading lines into driver then parallelize.
    from settings import RUN_LOCAL
    if RUN_LOCAL:
        lines = open(path, 'r', encoding='utf-8').readlines()
        return spark.read.json(spark.sparkContext.parallelize(lines))
    return spark.read.json(path)

def safe_parse_review(line: str) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

def extract_category_text(review: dict[str, Any]) -> tuple[str, str] | None:
    text = review.get(FIELD_REVIEW_TEXT)
    cat = review.get(FIELD_CATEGORY)
    if not text or not cat:
        return None
    return cat, text

def tokenize_text(text: str) -> list[str]:
    tokens = re.split(TOKEN_DELIMITER_PATTERN, text)
    return [t.lower() for t in tokens if t]

def filter_tokens(tokens: list[str], stopwords: set[str]) -> list[str]:
    return [t for t in tokens if len(t) >= MIN_TOKEN_LENGTH and t not in stopwords]

def compute_chi_square(N: int, Nc: int, Nt: int, Ntc: int) -> float:
    # chi-square on 2x2 document-presence contingency table
    # A = in-category docs with term, B = out-of-category docs with term
    # C = in-category docs without term, D = out-of-category docs without term
    A = Ntc
    B = Nt - Ntc
    C = Nc - Ntc
    D = N - Nc - Nt + Ntc
    denom = (A + B) * (C + D) * (A + C) * (B + D)
    if denom == 0:
        return 0.0
    return N * (A * D - B * C) ** 2 / denom

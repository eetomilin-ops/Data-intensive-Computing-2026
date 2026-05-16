# Shared utilities (load stopwords, helpers)
import re  # regex in tokenizer
from pathlib import Path

# JSON field names from Amazon review dataset
FIELD_REVIEW_TEXT = "reviewText"
FIELD_CATEGORY = "category"

# tokenization pattern - same as Task 1
TOKEN_DELIMITER_PATTERN = r"[\s\d\(\)\[\]\{\}\.\!\?\,\;\:\+\=\-_\"'`~#@&\*%€\$§\\/]+"
MIN_TOKEN_LENGTH = 2

def load_stopwords(stopwords_path: str | Path) -> set[str]:
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}

def _load_text_rdd(spark, path: str):
    # macOS lacks Hadoop native libs -- textFile/read.json fail with viewfs errors.
    # Bypass Hadoop FileSystem by reading into the driver, then parallelize.
    from settings import RUN_LOCAL
    if RUN_LOCAL:
        lines = open(path, 'r', encoding='utf-8').readlines()
        return spark.sparkContext.parallelize(lines)
    return spark.sparkContext.textFile(path)

def create_spark_session():
    from pyspark.sql import SparkSession
    from settings import SPARK_APP_NAME, SPARK_CONFIG
    
    builder = SparkSession.builder.appName(SPARK_APP_NAME)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    return builder.getOrCreate()

def load_reviews_df(spark, path: str):
    rdd = _load_text_rdd(spark, path)
    return spark.read.json(rdd)

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

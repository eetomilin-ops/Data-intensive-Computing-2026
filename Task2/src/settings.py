# Paths, constants, Spark configs
import os
from pathlib import Path

# local dev requires Java 21 (cluster uses Ubuntu 24.04 default)
# export JAVA_HOME=/usr/local/opt/openjdk@21

# runtime environment
RUN_LOCAL = os.getenv("RUN_LOCAL", "true").lower() == "true"

# base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# local dataset -- from data/extract_sample.sh
LOCAL_DEVSET = DATA_DIR / "reviews_devset_5k.json"
LOCAL_STOPWORDS = DATA_DIR / "stopwords.txt"

# cluster HDFS (confirmed 2026-05-14)
HDFS_DEVSET = "/dic_shared/amazon-reviews/full/reviews_devset.json"        # ~58 MB, for grading
# HDFS_FULL  = "/dic_shared/amazon-reviews/full/reviewscombined.json"       # ~58 GB, not required for T2

# active paths
DATASET_PATH = str(LOCAL_DEVSET.resolve()) if RUN_LOCAL else HDFS_DEVSET
STOPWORDS_PATH = str(LOCAL_STOPWORDS.resolve()) if RUN_LOCAL else str(LOCAL_STOPWORDS)

# Output paths
OUTPUT_RDD = str(OUTPUT_DIR / "output_rdd.txt")
OUTPUT_DS = str(OUTPUT_DIR / "output_ds.txt")
OUTPUT_METRICS = str(OUTPUT_DIR / "part3_metrics.json")
OUTPUT_COMPARISON = str(OUTPUT_DIR / "part3_comparison.txt")

# Spark configuration - local
SPARK_LOCAL_CONFIG = {
    "spark.master": "local[*]",
    "spark.driver.memory": "4g",
    "spark.executor.memory": "4g",
    "spark.sql.shuffle.partitions": "8",
}

# Spark configuration - cluster
SPARK_CLUSTER_CONFIG = {
    "spark.master": "yarn",
    "spark.submit.deployMode": "client",
    "spark.driver.memory": "8g",
    "spark.executor.memory": "8g",
    "spark.executor.instances": "4",
    "spark.sql.shuffle.partitions": "200",
}

# Active Spark config based on runtime
SPARK_CONFIG = SPARK_LOCAL_CONFIG if RUN_LOCAL else SPARK_CLUSTER_CONFIG
SPARK_APP_NAME = "Task2-Assignment2"

# Task parameters
TOP_TERMS_PER_CATEGORY = 75
CHI_SQUARE_FEATURES = 2000
RANDOM_SEED = 42

# Debug flag
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

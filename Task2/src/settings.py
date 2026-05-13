# Paths, constants, Spark configs
import os
from pathlib import Path

# Runtime environment switch
RUN_LOCAL = os.getenv("RUN_LOCAL", "true").lower() == "true"

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Dataset paths - local (priority: extracted sample, then Task1 dev parts)
_LOCAL_SAMPLE = DATA_DIR / "reviews_devset_5k.json"
_LOCAL_TASK1_PARTS = Path("../../Task1/requirements/Assets/reviews_devset.part_*.json")
LOCAL_DEVSET = str(_LOCAL_SAMPLE) if _LOCAL_SAMPLE.exists() else str(_LOCAL_TASK1_PARTS)

# stopwords - local copy first, fallback to Task1 assets
_LOCAL_STOP = DATA_DIR / "stopwords.txt"
_LOCAL_STOP_TASK1 = Path("../../Task1/requirements/Assets/stopwords.txt")
LOCAL_STOPWORDS = str(_LOCAL_STOP) if _LOCAL_STOP.exists() else str(_LOCAL_STOP_TASK1)

# Dataset paths - cluster HDFS
HDFS_DEVSET = "hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json"
HDFS_FULL = "hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json"
HDFS_USER_HOME = f"hdfs:///user/{os.getenv('USER', 'e12533692')}"

# Active dataset paths based on runtime
DATASET_PATH = LOCAL_DEVSET if RUN_LOCAL else HDFS_DEVSET
STOPWORDS_PATH = LOCAL_STOPWORDS

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

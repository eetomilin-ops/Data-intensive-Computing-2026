# Paths, constants, Spark configs

# Dataset paths
LOCAL_DEVSET_PARTS = "../Task1/requirements/Assets/reviews_devset.part_*.json"
LOCAL_STOPWORDS = "../Task1/requirements/Assets/stopwords.txt"
HDFS_DEVSET = "hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json"
HDFS_FULL = "hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json"

# Output paths
OUTPUT_DIR = "../output"
OUTPUT_RDD = f"{OUTPUT_DIR}/output_rdd.txt"
OUTPUT_DS = f"{OUTPUT_DIR}/output_ds.txt"
OUTPUT_METRICS = f"{OUTPUT_DIR}/part3_metrics.json"
OUTPUT_COMPARISON = f"{OUTPUT_DIR}/part3_comparison.txt"

# Spark configuration
SPARK_APP_NAME = "Task2-Assignment2"
SPARK_DRIVER_MEMORY = "4g"
SPARK_EXECUTOR_MEMORY = "4g"
SPARK_SHUFFLE_PARTITIONS = 200

# Task parameters
TOP_TERMS_PER_CATEGORY = 75
CHI_SQUARE_FEATURES = 2000
RANDOM_SEED = 42

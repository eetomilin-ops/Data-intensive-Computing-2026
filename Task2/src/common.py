# Shared utilities (load stopwords, helpers)

def load_stopwords(stopwords_path: str) -> set[str]:
    with open(stopwords_path, 'r') as f:
        return set(line.strip().lower() for line in f if line.strip())

def create_spark_session(app_name: str, driver_mem: str, executor_mem: str):
    from pyspark.sql import SparkSession
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.driver.memory", driver_mem) \
        .config("spark.executor.memory", executor_mem) \
        .getOrCreate()

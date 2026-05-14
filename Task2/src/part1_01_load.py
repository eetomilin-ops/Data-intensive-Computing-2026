# read JSON review dataset as RDD of (category, reviewText) pairs
import json
from settings import RUN_LOCAL

def load_reviews_rdd(spark, path: str):
    from common import FIELD_CATEGORY, FIELD_REVIEW_TEXT

    # on local, read via Python to avoid Hadoop GlobFilter issues with [] in paths
    if RUN_LOCAL:
        lines = open(path, 'r', encoding='utf-8').readlines()
        rdd = spark.sparkContext.parallelize(lines)
    else:
        rdd = spark.sparkContext.textFile(path)

    parsed = rdd.map(json.loads)
    filtered = parsed.filter(lambda r: r.get(FIELD_CATEGORY) and r.get(FIELD_REVIEW_TEXT))
    return filtered.map(lambda r: (r[FIELD_CATEGORY], r[FIELD_REVIEW_TEXT]))

# read JSON review dataset as RDD of (category, reviewText) pairs
import json
from common import FIELD_CATEGORY, FIELD_REVIEW_TEXT, _load_text_rdd

def load_reviews_rdd(spark, path: str):
    rdd = _load_text_rdd(spark, path)
    parsed = rdd.map(json.loads)
    filtered = parsed.filter(lambda r: r.get(FIELD_CATEGORY) and r.get(FIELD_REVIEW_TEXT))
    return filtered.map(lambda r: (r[FIELD_CATEGORY], r[FIELD_REVIEW_TEXT]))

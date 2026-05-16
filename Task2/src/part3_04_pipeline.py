# Full Part 3 pipeline: Part 2 stages + Normalizer + OneVsRest(LinearSVC).
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer
from common import FIELD_CATEGORY

def build_part3_pipeline(
    tokenizer,
    stopwords_remover,
    vectorizer,
    idf,
    chi_selector,
    normalizer,
    classifier,
):
    indexer = StringIndexer(
        inputCol=FIELD_CATEGORY, outputCol="label", handleInvalid="skip"
    )
    return Pipeline(stages=[
        indexer,
        tokenizer,
        stopwords_remover,
        vectorizer,
        idf,
        chi_selector,
        normalizer,
        classifier,
    ])

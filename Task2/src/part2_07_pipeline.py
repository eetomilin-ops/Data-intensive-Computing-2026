# Chain all Part 2 stages into a Spark ML Pipeline, fit on the review DataFrame.
# Adds a StringIndexer for the category column so ChiSqSelector gets numeric labels.
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer
from common import FIELD_CATEGORY

def build_part2_pipeline(
    df,
    tokenizer,
    stopwords_remover,
    vectorizer,
    idf,
    chi_selector,
):
    indexer = StringIndexer(
        inputCol=FIELD_CATEGORY, outputCol="label", handleInvalid="skip"
    )
    pipeline = Pipeline(stages=[
        indexer,
        tokenizer,
        stopwords_remover,
        vectorizer,
        idf,
        chi_selector,
    ])
    return pipeline.fit(df)

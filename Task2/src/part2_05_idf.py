# IDF -- weights raw term frequencies by inverse document frequency.
from pyspark.ml.feature import IDF

def create_idf(
    input_col: str = "raw_features",
    output_col: str = "tfidf_features",
):
    return IDF(inputCol=input_col, outputCol=output_col)

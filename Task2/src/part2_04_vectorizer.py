# CountVectorizer -- converts token arrays to term-frequency vectors.
# No vocab limit here; chi-square selection reduces dimensionality later.
from pyspark.ml.feature import CountVectorizer

def create_count_vectorizer(
    input_col: str = "filtered",
    output_col: str = "raw_features",
):
    return CountVectorizer(
        inputCol=input_col,
        outputCol=output_col,
        minDF=1.0,
    )

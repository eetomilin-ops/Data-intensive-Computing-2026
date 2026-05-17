# CountVectorizer -- converts token arrays to term-frequency vectors.
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

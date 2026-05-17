# CountVectorizer -- converts token arrays to term-frequency vectors.
# vocabSize caps vocabulary to most frequent terms, speeding up IDF + SVM.
from pyspark.ml.feature import CountVectorizer

def create_count_vectorizer(
    input_col: str = "filtered",
    output_col: str = "raw_features",
    vocab_size: int = 15000,
):
    return CountVectorizer(
        inputCol=input_col,
        outputCol=output_col,
        vocabSize=vocab_size,
        minDF=1.0,
    )

# StopWordsRemover -- filters stopwords and single-character tokens
from pyspark.ml.feature import StopWordsRemover

def create_stopwords_remover(
    stopwords: list[str],
    input_col: str = "tokens",
    output_col: str = "filtered",
):
    # StopWordsRemover has no min-token-length parameter. Add all single
    # lowercase chars to the stopword list so one pass catches both cases.
    full = set(stopwords)
    for c in range(ord('a'), ord('z') + 1):
        full.add(chr(c))
    return StopWordsRemover(
        stopWords=list(full),
        caseSensitive=False,
        inputCol=input_col,
        outputCol=output_col,
    )

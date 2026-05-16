# RegexTokenizer using Task 1 delimiter pattern -- splits on whitespace, digits,
# and punctuation ()[]{}.!?,;:+=-_\"'`~#@&*%$\/. Applies casefolding.
from pyspark.ml.feature import RegexTokenizer
from common import TOKEN_DELIMITER_PATTERN, FIELD_REVIEW_TEXT

def create_tokenizer(
    input_col: str = FIELD_REVIEW_TEXT,
    output_col: str = "tokens",
):
    return RegexTokenizer(
        pattern=TOKEN_DELIMITER_PATTERN,
        gaps=True,
        inputCol=input_col,
        outputCol=output_col,
        toLowercase=True,
    )

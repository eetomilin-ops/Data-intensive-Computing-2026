# ChiSqSelector -- picks top-k terms by chi-square score against the label.
# Requires a numeric label column (category -> label via StringIndexer upstream).
from pyspark.ml.feature import ChiSqSelector

def create_chi_selector(
    num_features: int = 2000,
    features_col: str = "tfidf_features",
    label_col: str = "label",
    output_col: str = "selected_features",
):
    return ChiSqSelector(
        numTopFeatures=num_features,
        featuresCol=features_col,
        labelCol=label_col,
        outputCol=output_col,
    )

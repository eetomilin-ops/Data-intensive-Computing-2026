# L2 vector normalizer -- applied before SVM to make feature scales comparable.
from pyspark.ml.feature import Normalizer

def create_normalizer(
    input_col: str = "selected_features",
    output_col: str = "norm_features",
):
    return Normalizer(p=2.0, inputCol=input_col, outputCol=output_col)

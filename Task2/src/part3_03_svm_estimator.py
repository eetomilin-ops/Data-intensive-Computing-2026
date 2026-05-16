# Multi-class SVM via OneVsRest wrapper around LinearSVC.
# The inner LinearSVC params (regParam, standardization, maxIter) are exposed
# through getClassifier() for ParamGridBuilder.
from pyspark.ml.classification import LinearSVC, OneVsRest

def create_svm(
    features_col: str = "norm_features",
    label_col: str = "label",
    prediction_col: str = "prediction",
):
    svc = LinearSVC(featuresCol=features_col, labelCol=label_col, predictionCol=prediction_col)
    return OneVsRest(classifier=svc, featuresCol=features_col, labelCol=label_col, predictionCol=prediction_col)

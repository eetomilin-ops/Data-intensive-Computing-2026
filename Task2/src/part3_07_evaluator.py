# F1 score evaluator for multi-class classification.
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

def create_evaluator(
    label_col: str = "label",
    prediction_col: str = "prediction",
):
    return MulticlassClassificationEvaluator(
        labelCol=label_col,
        predictionCol=prediction_col,
        metricName="f1",
    )

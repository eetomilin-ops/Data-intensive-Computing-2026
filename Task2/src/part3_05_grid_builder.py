# 24 grid points: 2 chi-square × 3 regParam × 2 standardization × 2 maxIter.
from pyspark.ml.tuning import ParamGridBuilder

def build_param_grid(chi_selector, ovr_classifier):
    svc = ovr_classifier.getClassifier()
    return ParamGridBuilder() \
        .addGrid(chi_selector.numTopFeatures, [2000, 500]) \
        .addGrid(svc.regParam, [0.01, 0.1, 1.0]) \
        .addGrid(svc.standardization, [True, False]) \
        .addGrid(svc.maxIter, [50, 100]) \
        .build()

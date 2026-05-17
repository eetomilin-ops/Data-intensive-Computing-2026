# 2-fold cross-validation. parallelism=1 avoids Python multiprocessing pool
# issues on macOS (pool.imap_unordered + deque incompatibility with PySpark).
from pyspark.ml.tuning import CrossValidator

def create_cross_validator(
    pipeline,
    param_grid,
    evaluator,
    num_folds: int = 2,
    seed: int = 42,
):
    return CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=param_grid,
        evaluator=evaluator,
        numFolds=num_folds,
        parallelism=2,  # adjust for multi-cores. it's for my laptop. If set too much spark begins to dump -> slows
        seed=seed,
    )

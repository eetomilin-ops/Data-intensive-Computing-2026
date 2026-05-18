# Reproducible train/validation/test split.
from pyspark.sql import DataFrame

from settings import RANDOM_SEED


def split_data(
    df: DataFrame,
    weights: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = RANDOM_SEED,
):
    splits = df.randomSplit(list(weights), seed=seed)
    return splits[0], splits[1], splits[2]

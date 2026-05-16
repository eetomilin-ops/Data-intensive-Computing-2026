# Part 3: Multi-class SVM classifier with grid search over 24 configs.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_spark_session, load_stopwords, load_reviews_df
from settings import DATASET_PATH, STOPWORDS_PATH, OUTPUT_METRICS, RANDOM_SEED
from part2_02_tokenizer import create_tokenizer
from part2_03_stopwords import create_stopwords_remover
from part2_04_vectorizer import create_count_vectorizer
from part2_05_idf import create_idf
from part2_06_chi_selector import create_chi_selector
from part3_01_data_split import split_data
from part3_02_normalizer import create_normalizer
from part3_03_svm_estimator import create_svm
from part3_04_pipeline import build_part3_pipeline
from part3_05_grid_builder import build_param_grid
from part3_06_cross_validator import create_cross_validator
from part3_07_evaluator import create_evaluator
from part3_08_output import save_metrics

if __name__ == "__main__":
    spark = create_spark_session()
    try:
        spark.sparkContext.setLogLevel('WARN')

        stopwords = load_stopwords(STOPWORDS_PATH)
        print(f"Stopwords: {len(stopwords)}")

        df = load_reviews_df(spark, DATASET_PATH)
        train, val, test = split_data(df, seed=RANDOM_SEED)
        # 24 configs × 2 folds = 48 fits. Caching train_val avoids re-reading
        # JSON on each fit. parallelism=1 in CrossValidator avoids macOS
        # multiprocessing pool incompatibility with PySpark.
        train_val = train.union(val).cache()
        print(f"Train+val : {train_val.count()}  Test: {test.count()}")

        tokenizer   = create_tokenizer()
        sw_remover  = create_stopwords_remover(list(stopwords))
        vectorizer  = create_count_vectorizer()
        idf         = create_idf()
        chi_sel     = create_chi_selector()
        normalizer  = create_normalizer()
        ovr_svm     = create_svm()

        pipeline    = build_part3_pipeline(tokenizer, sw_remover, vectorizer, idf, chi_sel, normalizer, ovr_svm)
        param_grid  = build_param_grid(chi_sel, ovr_svm)
        evaluator   = create_evaluator()
        cv          = create_cross_validator(pipeline, param_grid, evaluator)

        n_fits = len(param_grid) * 2  # 2 folds
        print(f"Grid size : {len(param_grid)} configs, 2-fold CV ({n_fits} fits)")
        print(f"Spark UI  : http://localhost:4040  (track stages/jobs there)")
        print("Fitting...", flush=True)
        cv_model = cv.fit(train_val)
        print("done.")

        best_f1 = max(cv_model.avgMetrics)
        print(f"Best F1   : {best_f1:.4f}")

        # final evaluation on held-out test set
        test_preds = cv_model.transform(test)
        test_f1 = evaluator.evaluate(test_preds)
        print(f"Test F1   : {test_f1:.4f}")

        save_metrics(cv_model, OUTPUT_METRICS)
        print(f"Metrics   : {OUTPUT_METRICS}")
        print("Part 3 done.")
    finally:
        spark.stop()

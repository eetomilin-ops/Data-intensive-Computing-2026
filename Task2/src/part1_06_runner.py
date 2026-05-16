# Part 1: RDD-based chi-square feature selection, matching Task 1 output format
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_spark_session, load_stopwords
from settings import DATASET_PATH, STOPWORDS_PATH, OUTPUT_RDD, TOP_TERMS_PER_CATEGORY, RUN_LOCAL

if __name__ == "__main__":
    spark = create_spark_session()
    try:
        sc = spark.sparkContext
        sc.setLogLevel('WARN')

        # ship source modules to workers so flatMap/map lambdas can import them.
        # Not needed in local mode -- all code runs in the driver process.
        if not RUN_LOCAL:
            src_dir = Path(__file__).parent
            for mod in ['common.py', 'part1_03_chi_square.py', 'part1_02_tokenize.py',
                        'part1_01_load.py', 'part1_04_aggregate.py', 'part1_05_output.py']:
                sc.addPyFile(str(src_dir / mod))

        from part1_01_load import load_reviews_rdd
        from part1_02_tokenize import tokenize_document
        from part1_03_chi_square import count_and_score
        from part1_04_aggregate import select_top_k_per_category, merge_all_terms
        from part1_05_output import write_output

        print(f"Dataset  : {DATASET_PATH}")
        print(f"Stopwords: {STOPWORDS_PATH}")

        stopwords = load_stopwords(STOPWORDS_PATH)
        print(f"Stopwords loaded: {len(stopwords)}")

        raw = load_reviews_rdd(spark, DATASET_PATH)

        tokenized = raw.map(lambda r: tokenize_document(r, stopwords))

        scored = count_and_score(tokenized)
        print(f"Scored pairs  : {scored.count()}")

        top = select_top_k_per_category(scored, TOP_TERMS_PER_CATEGORY)
        print(f"Categories    : {len(top)}")

        merged = merge_all_terms(top)
        print(f"Merged terms  : {len(merged)}")

        write_output(top, merged, OUTPUT_RDD)
        print(f"Output written: {OUTPUT_RDD}")

        print("Task 1 completed.")
    finally:
        spark.stop()

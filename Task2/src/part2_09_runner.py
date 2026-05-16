# Part 2: DataFrame-based TF-IDF pipeline with chi-square feature selection
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_spark_session, load_stopwords, load_reviews_df, write_text_file
from settings import DATASET_PATH, STOPWORDS_PATH, OUTPUT_DS, CHI_SQUARE_FEATURES
from part2_02_tokenizer import create_tokenizer
from part2_03_stopwords import create_stopwords_remover
from part2_04_vectorizer import create_count_vectorizer
from part2_05_idf import create_idf
from part2_06_chi_selector import create_chi_selector
from part2_07_pipeline import build_part2_pipeline
from part2_08_output import extract_selected_terms, save_terms

if __name__ == "__main__":
    spark = create_spark_session()
    try:
        spark.sparkContext.setLogLevel('WARN')

        print(f"Dataset  : {DATASET_PATH}")
        stopwords = load_stopwords(STOPWORDS_PATH)
        print(f"Stopwords: {len(stopwords)}")

        df = load_reviews_df(spark, DATASET_PATH)
        print(f"Reviews  : {df.count()}")

        tokenizer   = create_tokenizer()
        sw_remover  = create_stopwords_remover(list(stopwords))
        vectorizer  = create_count_vectorizer()
        idf         = create_idf()
        chi_sel     = create_chi_selector(num_features=CHI_SQUARE_FEATURES)

        model = build_part2_pipeline(df, tokenizer, sw_remover, vectorizer, idf, chi_sel)
        terms = extract_selected_terms(model)
        print(f"Selected : {len(terms)} terms")

        save_terms(spark, terms, OUTPUT_DS)
        print(f"Output   : {OUTPUT_DS}")
        print("Part 2 done.")
    finally:
        spark.stop()

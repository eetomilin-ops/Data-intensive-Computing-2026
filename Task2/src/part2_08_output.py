# Extract selected terms from the fitted Part 2 pipeline and write output_ds.txt.
from common import write_text_file

# pipeline stage positions (order from part2_07_pipeline)
_IDX_COUNT_VECTORIZER = 3
_IDX_CHI_SELECTOR     = 5

def extract_selected_terms(pipeline_model) -> list[str]:
    vocab = pipeline_model.stages[_IDX_COUNT_VECTORIZER].vocabulary
    indices = pipeline_model.stages[_IDX_CHI_SELECTOR].selectedFeatures
    return [vocab[i] for i in indices]

def save_terms(spark, terms: list[str], output_path: str):
    write_text_file(spark, terms, output_path)

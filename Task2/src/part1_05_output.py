# write output_rdd.txt in the required Task 1 format
from common import write_text_file

def write_output(
    spark,
    category_terms: dict[str, list[tuple[str, float]]],
    merged_terms: list[str],
    output_path: str,
):
    lines = []
    for cat in sorted(category_terms):
        lines.append(cat + ' ' + ' '.join(f"{t}:{s:.4f}" for t, s in category_terms[cat]))
    lines.append(' '.join(merged_terms))
    write_text_file(spark, lines, output_path)

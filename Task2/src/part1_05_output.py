# write output_rdd.txt in the required Task 1 format
import os

def write_output(
    category_terms: dict[str, list[tuple[str, float]]],
    merged_terms: list[str],
    output_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for cat in sorted(category_terms):
            line = cat + ' ' + ' '.join(f"{t}:{s:.4f}" for t, s in category_terms[cat])
            f.write(line + '\n')
        f.write(' '.join(merged_terms) + '\n')

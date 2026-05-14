# select top-k terms per category by chi-square score, then merge alphabetically

def select_top_k_per_category(chi_square_rdd, k: int) -> dict[str, list[tuple[str, float]]]:
    # group (cat, term, score) by category, sort by score desc then term asc, take top k
    def top_k(it, k):
        # heap would be more memory-friendly, but k=75 is small enough
        sorted_items = sorted(it, key=lambda x: (-x[1], x[0]))
        return sorted_items[:k]

    return (
        chi_square_rdd
        .map(lambda r: (r[0], (r[1], r[2])))         # (cat, (term, score))
        .groupByKey()
        .mapValues(lambda vs: top_k(vs, k))
        .collectAsMap()
    )

def merge_all_terms(category_terms: dict[str, list[tuple[str, float]]]) -> list[str]:
    # collect every unique term across all categories, sort alphabetically
    all_terms = set()
    for pairs in category_terms.values():
        all_terms |= {t for t, _ in pairs}
    return sorted(all_terms)

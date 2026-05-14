# compute chi-square values for all (category, term) pairs using document-presence
from common import compute_chi_square

def count_and_score(rdd):
    # emit with plain lambdas so no module-level symbol references are serialized
    emitted = rdd.flatMap(
        lambda ct: (
            [(("__N__", "__N__"), 1), (("__NC__", ct[0]), 1)]
            + [(("__NT__", t), 1) for t in ct[1]]
            + [((ct[0], t), 1) for t in ct[1]]
        )
    )

    counts = emitted.reduceByKey(lambda a, b: a + b).collectAsMap()

    N  = counts.get(("__N__", "__N__"), 0)
    Nc = {k[1]: v for (k, v) in counts.items() if k[0] == "__NC__"}
    Nt = {k[1]: v for (k, v) in counts.items() if k[0] == "__NT__"}

    sentinel = {"__N__", "__NC__", "__NT__"}
    term_cat_pairs = [
        (cat, term, compute_chi_square(N, Nc.get(cat, 0), Nt.get(term, 0), cnt))
        for (cat, term), cnt in counts.items()
        if cat not in sentinel and term not in sentinel
    ]

    return rdd.context.parallelize(term_cat_pairs)

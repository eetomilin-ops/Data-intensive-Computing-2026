# compute chi-square values for all (category, term) pairs using document-presence
from common import compute_chi_square

# one reduceByKey pass is cheaper than multiple scans over the data
KEY_N  = "__N__"
KEY_NC = "__NC__"
KEY_NT = "__NT__"

def _emit_counters(cat_terms):
    category, term_set = cat_terms
    counters = [( (KEY_N, KEY_N), 1), ((KEY_NC, category), 1)]
    for term in term_set:
        counters.append(((KEY_NT, term), 1))
        counters.append(((category, term), 1))
    return counters

def count_and_score(rdd):
    emitted = rdd.flatMap(_emit_counters)
    counts = emitted.reduceByKey(lambda a, b: a + b).collectAsMap()

    N  = counts.get((KEY_N, KEY_N), 0)
    Nc = {}  # {category: doc_count}
    Nt = {}  # {term: doc_count}
    term_cat_data = []  # (category, term, Ntc)

    for (prefix, value), cnt in counts.items():
        if prefix == KEY_NC:
            Nc[value] = cnt
        elif prefix == KEY_NT:
            Nt[value] = cnt
        elif prefix != KEY_N and value != KEY_N:
            # not a sentinel -- genuine (category, term) pair
            term_cat_data.append((prefix, value, cnt))

    scored = []
    for cat, term, Ntc in term_cat_data:
        score = compute_chi_square(N, Nc.get(cat, 0), Nt.get(term, 0), Ntc)
        scored.append((cat, term, score))

    return rdd.context.parallelize(scored)

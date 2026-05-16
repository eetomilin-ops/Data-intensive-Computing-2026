# Chi-square feature selection on document-presence counts.
#
# Data flow:
#   RDD[(category, set[term])]        -- one set per review, terms deduplicated
#       |  _emit_counters             -- explode each doc into tagged counter tuples
#       v
#   RDD[((prefix, key), 1)]           -- e.g. (("__NC__", "Books"), 1)
#       |  reduceByKey                -- sum all ones per (prefix, key)
#       v
#   dict{(prefix, key): count}        -- collected to driver, small in practice
#       |  count_and_score            -- demux sentinel keys, compute chi-square
#       v
#   RDD[(category, term, chi2)]       -- every (cat, term) pair with its score
#
# All four counters needed for the 2x2 chi-square contingency table are collected in a single reduceByKey pass over the raw data.

from common import compute_chi_square

KEY_N  = "__N__"   # total review documents N
KEY_NC = "__NC__"  # documents per category Nc
KEY_NT = "__NT__"  # documents containing term Nt

def _emit_counters(cat_terms   # ("Books", {"author", "plot", "reading"})
                   ):          # explode one review document into tagged counter tuples.
    category, term_set = cat_terms
    counters = [( (KEY_N, KEY_N), 1), ((KEY_NC, category), 1)]
    for term in term_set:
        counters.append(((KEY_NT, term), 1))
        counters.append(((category, term), 1))
    return counters

def count_and_score(rdd  # RDD[(category, set[term])]  -- from tokenize + dedup step
                    ):

#    The intermediate counts dict is collected to the driver because the number
#    of unique (prefix, key) pairs equals (1 + C + T + C*T pairs that co-occur),
#    which for this dataset is manageable in driver memory.

    # collected to driver -- safe on devset (~5k reviews, bounded term count).
    # Would need a shuffle-based approach on the full 58 GB dataset.
    emitted = rdd.flatMap(_emit_counters)
    counts = emitted.reduceByKey(lambda a, b: a + b).collectAsMap()

    N  = counts.get((KEY_N, KEY_N), 0)
    Nc = {}              # {category: doc_count}
    Nt = {}              # {term: doc_count}
    term_cat_data = []   # [(category, term, Ntc), ...]

    for (prefix, value), cnt in counts.items():
        if prefix == KEY_NC:
            Nc[value] = cnt
        elif prefix == KEY_NT:
            Nt[value] = cnt
        elif prefix != KEY_N and value != KEY_N:
            term_cat_data.append((prefix, value, cnt))

    scored = []  #  RDD[(category, term, chi2)] -- one record per (cat, term) pair ("Books", "author", 479.63)
    for cat, term, Ntc in term_cat_data:
        score = compute_chi_square(N, Nc.get(cat, 0), Nt.get(term, 0), Ntc)
        scored.append((cat, term, score))

    return rdd.context.parallelize(scored)

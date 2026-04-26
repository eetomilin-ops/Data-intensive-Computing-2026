import json
from mrjob.job import MRJob
from mrjob.step import MRStep
from common import compute_chi_square, format_term_score, update_top_k
from settings import (
    COUNTER_TAG_CATEGORY_DOCS, COUNTER_TAG_TERM_CATEGORY_DOCS,
    COUNTER_TAG_TERM_DOCS, COUNTER_TAG_TOTAL_DOCS, DEFAULT_META_FILENAME,
)

# this job reads the count output from CountStatsJob and a small meta.json
# that carries N and all Nc values (written between the two jobs by build_output).
#
# mapper re-keys records so the reducer can group NT and NTC together per term:
#   NT  records  -> keyed by term        so the reducer sees all categories for that term
#   NTC records  -> keyed by term        joined with NT in the same reduce group
#   N / NC are loaded from meta.json before the reduce phase, not shuffled
#
# reducer emits: (category, "term:score") for each term in each category
# reducer_final flushes the bounded heaps as final ranked lines
class ScoreTopKJob(MRJob):
    def configure_args(self):
        super().configure_args()
        self.add_file_arg("--meta", help="path to meta.json from CountStatsJob")

    def steps(self):
        return [MRStep(
            mapper=self.mapper,
            reducer_init=self.reducer_init,
            reducer=self.reducer,
            reducer_final=self.reducer_final,
        )]

    def mapper(self, _, line):
        try:
            key, value = json.loads(line)
        except (ValueError, TypeError): return
        tag = key[0]
        if tag == COUNTER_TAG_TERM_DOCS:
            # re-key by term so NT and NTC land in the same reducer group
            term = key[1]
            yield term, (COUNTER_TAG_TERM_DOCS, None, int(value))
        elif tag == COUNTER_TAG_TERM_CATEGORY_DOCS:
            cat, term = key[1], key[2]
            yield term, (COUNTER_TAG_TERM_CATEGORY_DOCS, cat, int(value))

    def reducer_init(self):
        with open(self.options.meta, encoding="utf-8") as f:
            meta = json.load(f)
        self.N      = meta["N"]                     # total docs
        self.Nc     = meta["Nc"]                    # {category: doc_count}
        # one heap per category, filled as each term group is processed
        self.heaps  = {cat: [] for cat in self.Nc}

    def reducer(self, term, values):
        Nt   = 0
        ntcs = {}
        for tag, cat, count in values:
            if tag == COUNTER_TAG_TERM_DOCS:
                Nt = count
            else:
                ntcs[cat] = count
        # score this term against every category where it appeared
        for cat, Ntc in ntcs.items():
            if cat not in self.heaps: continue
            score = compute_chi_square(self.N, self.Nc[cat], Nt, Ntc)
            update_top_k(self.heaps[cat], score, term)
        return
        yield  # make this a generator so mrjob treats it correctly

    def reducer_final(self):
        for cat in sorted(self.heaps):
            heap = self.heaps[cat]
            # sort descending by score for the output line
            ranked = sorted(heap, key=lambda x: x[0], reverse=True)
            terms_str = " ".join(format_term_score(t, s) for s, t in ranked)
            yield cat, terms_str

if __name__ == "__main__":
    ScoreTopKJob.run()
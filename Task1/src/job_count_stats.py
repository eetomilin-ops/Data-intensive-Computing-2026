from mrjob.job import MRJob
from mrjob.step import MRStep
from common import (
    compile_tokenizer, extract_required_fields, filter_tokens,
    load_stopwords, safe_parse_review, unique_terms_for_document,
)
from settings import (
    COUNTER_TAG_CATEGORY_DOCS, COUNTER_TAG_TERM_CATEGORY_DOCS,
    COUNTER_TAG_TERM_DOCS, COUNTER_TAG_TOTAL_DOCS,
)

# emitted key shapes:
#   (N,)          -> global doc count
#   (NC, cat)     -> docs in category
#   (NT, term)    -> docs containing term (across all categories)
#   (NTC, cat, term) -> docs in category containing term
class CountStatsJob(MRJob):
    def steps(self):
        return [MRStep(
            mapper_init=self.mapper_init,
            mapper=self.mapper,
            combiner=self.combiner,
            reducer=self.reducer,
        )]

    def mapper_init(self):
        # load once per mapper process, not once per line
        self.stopwords = load_stopwords()
        self.split     = compile_tokenizer()

    def mapper(self, _, line):
        review = safe_parse_review(line)
        if review is None: return
        parsed = extract_required_fields(review)
        if parsed is None: return
        cat, text = parsed
        terms = unique_terms_for_document(
            filter_tokens(
                [t.lower() for t in self.split(text) if t],
                self.stopwords,
            )
        )
        yield (COUNTER_TAG_TOTAL_DOCS,), 1
        yield (COUNTER_TAG_CATEGORY_DOCS, cat), 1
        for term in terms:
            yield (COUNTER_TAG_TERM_DOCS, term), 1
            yield (COUNTER_TAG_TERM_CATEGORY_DOCS, cat, term), 1

    def combiner(self, key, values):
        yield key, sum(values)

    def reducer(self, key, values):
        yield key, sum(values)

if __name__ == "__main__":
    CountStatsJob.run()
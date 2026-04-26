"""First mrjob stage for raw document counting."""

from typing import Iterable


class CountStatsJob:
    """Input: raw review lines from local files or HDFS.
    Output: tagged count records for global, category, term, and term-category statistics.
    Purpose: aggregate all required count statistics in a single raw-data scan.
    """

    def mapper_init(self) -> None:
        """Input: no per-record input.
        Output: initialized mapper state.
        Purpose: prepare stopwords and tokenizer once per mapper process.
        """
        pass

    def mapper(self, _: object, line: str) -> Iterable[tuple[tuple[str, ...], int]]:
        """Input: ignored key and one raw dataset line.
        Output: tagged count tuples for downstream aggregation.
        Purpose: emit document-presence counts derived from one review.
        """
        pass

    def combiner(self, key: tuple[str, ...], values: Iterable[int]) -> Iterable[tuple[tuple[str, ...], int]]:
        """Input: tagged count key and partial integer counts.
        Output: locally aggregated count tuples.
        Purpose: reduce shuffle volume before the reducer phase.
        """
        pass

    def reducer(self, key: tuple[str, ...], values: Iterable[int]) -> Iterable[tuple[tuple[str, ...], int]]:
        """Input: tagged count key and aggregated integer counts.
        Output: final count record for that key.
        Purpose: finalize global and per-category statistics needed by later stages.
        """
        pass
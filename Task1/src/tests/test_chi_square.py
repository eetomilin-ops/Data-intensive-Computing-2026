"""Test stubs for scoring and ranking behavior."""


# ranking bugs are easier to catch on a tiny grouped fixture
def test_score_top_k_job_ranking_order(
) -> None:                                 # assertion-only unit test
    pass


# top-k trimming must stay exact even if more candidates arrive
def test_score_top_k_job_respects_limit(
) -> None:                                  # assertion-only unit test
    pass
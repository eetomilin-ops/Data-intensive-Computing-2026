import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import compute_chi_square, update_top_k

# feed three terms with known ordering, verify heap reflects it
def test_score_top_k_job_ranking_order():
    heap = []
    update_top_k(heap, 0.5, "apple")
    update_top_k(heap, 9.1, "banana")
    update_top_k(heap, 3.2, "cherry")
    # highest score should survive after sorting descending
    ranked = sorted(heap, key=lambda x: x[0], reverse=True)
    assert ranked[0][1] == "banana"
    assert ranked[-1][1] == "apple"

# heap must not grow beyond the given limit
def test_score_top_k_job_respects_limit():
    heap = []
    for i in range(10):
        update_top_k(heap, float(i), f"term{i}", k=3)
    assert len(heap) == 3
    # only the top 3 scores (7, 8, 9) should remain
    scores = sorted(s for s, _ in heap)
    assert scores == [7.0, 8.0, 9.0]
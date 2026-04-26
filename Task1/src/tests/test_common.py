import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import (
    safe_parse_review, extract_required_fields,
    compile_tokenizer, tokenize, filter_tokens,
    unique_terms_for_document, compute_chi_square,
)
from settings import STOPWORDS_PATH

# one valid line from the dev set, one broken line
VALID_LINE = json.dumps({
    "reviewerID": "X1", "asin": "B001",
    "reviewText": "Great hose, easy to use!",
    "overall": 5.0, "summary": "Good",
    "unixReviewTime": 0, "reviewTime": "01 1, 2020",
    "category": "Patio_Lawn_and_Garde"
})

def test_safe_parse_review():
    assert safe_parse_review(VALID_LINE) is not None
    assert safe_parse_review("not json{") is None
    assert safe_parse_review("") is None

def test_tokenize_and_filter_tokens():
    stopwords = {"to", "a", "the", "is", "and"}
    split = compile_tokenizer()
    tokens = tokenize("Great hose, easy to use!", split)
    filtered = filter_tokens(tokens, stopwords)
    assert "great" in filtered
    assert "to" not in filtered       # stopword removed
    assert "a" not in filtered
    assert all(len(t) >= 2 for t in filtered)

def test_unique_terms_for_document():
    terms = unique_terms_for_document(["hose", "great", "hose", "easy"])
    assert terms == {"hose", "great", "easy"}  # deduped

# known values computed by hand for a tiny 2x2 table
def test_compute_chi_square():
    # N=100, Nc=50, Nt=20, Ntc=15
    score = compute_chi_square(100, 50, 20, 15)
    assert score > 0
    # degenerate case: term never appears -> score should be 0
    assert compute_chi_square(100, 50, 0, 0) == 0.0
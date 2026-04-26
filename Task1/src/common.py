import json
import re
import heapq
from pathlib import Path
from typing import Any, Callable, Iterable
from settings import MIN_TOKEN_LENGTH, STOPWORDS_PATH, TOKEN_DELIMITER_PATTERN, TOP_K_TERMS

def load_stopwords(path: str | Path = STOPWORDS_PATH) -> set[str]:
    with open(path, encoding="utf-8") as f:
        return {w.strip().lower() for w in f if w.strip()}

# compile once; reuse the returned callable across all records in a mapper
def compile_tokenizer() -> Callable[[str], list[str]]:
    return re.compile(TOKEN_DELIMITER_PATTERN).split

def tokenize(text: str, split_fn: Callable[[str], list[str]]) -> list[str]:
    return [t.lower() for t in split_fn(text) if t]

def filter_tokens(tokens: list[str], stopwords: set[str]) -> list[str]:
    return [t for t in tokens if len(t) >= MIN_TOKEN_LENGTH and t not in stopwords]

def safe_parse_review(line: str) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

def extract_required_fields(review: dict[str, Any]) -> tuple[str, str] | None:
    text = review.get("reviewText")
    cat  = review.get("category")
    if not text or not cat: return None
    return cat, text

def unique_terms_for_document(tokens: Iterable[str]) -> set[str]:
    return set(tokens)

# chi-square on a 2x2 document-presence contingency table:
#   A = in-category docs with term      B = out-of-category docs with term
#   C = in-category docs without term   D = out-of-category docs without term
def compute_chi_square(N: int, Nc: int, Nt: int, Ntc: int) -> float:
    A = Ntc
    B = Nt - Ntc
    C = Nc - Ntc
    D = N - Nc - Nt + Ntc
    denom = (A + B) * (C + D) * (A + C) * (B + D)
    if denom == 0: return 0.0
    return N * (A * D - B * C) ** 2 / denom

# min-heap bounded to k: push candidate, evict the weakest when over limit
def update_top_k(heap: list, score: float, term: str, k: int = TOP_K_TERMS) -> None:
    heapq.heappush(heap, (score, term))
    if len(heap) > k: heapq.heappop(heap)

def format_term_score(term: str, score: float) -> str:
    return f"{term}:{score:.4f}"
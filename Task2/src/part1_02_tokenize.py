# tokenize review text, apply stopwords, deduplicate per document (document-presence)
from common import tokenize_text, filter_tokens

def tokenize_document(cat_text: tuple[str, str], stopwords: set[str]) -> tuple[str, set[str]]:
    cat, text = cat_text
    tokens = tokenize_text(text)
    cleaned = filter_tokens(tokens, stopwords)
    return cat, set(cleaned)

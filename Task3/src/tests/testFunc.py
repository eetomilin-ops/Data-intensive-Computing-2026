# Pure business-logic tests. No MiniStack, no boto3, no network.
# Run: pytest tests/test_functional.py

# preprocess adds tokenised, lemmatised, stopword-free token list
def testPreprocessAddsTokens(reviewClean):
    from common import preprocess

    result = preprocess(reviewClean)
    assert "tokens" in result
    assert isinstance(result["tokens"], list)
    assert len(result["tokens"]) > 0
    # original fields preserved
    assert result["reviewerID"] == reviewClean["reviewerID"]


def testPreprocessRemovesStopwords(reviewClean):
    from common import preprocess

    result = preprocess(reviewClean)
    tokensLower = {t.lower() for t in result["tokens"]}
    # common English stopwords must be absent
    for sw in ["the", "a", "is", "and", "it", "this", "with", "was"]:
        assert sw not in tokensLower, f"stopword '{sw}' not removed"


def testPreprocessLemmatises(reviewClean):
    from common import preprocess

    result = preprocess(reviewClean)
    tokensLower = {t.lower() for t in result["tokens"]}
    # "bought" -> "buy", "works" -> "work"
    assert "buy" in tokensLower or "bought" not in tokensLower


# profanityCheck detects bad words
def testProfanityDetectsBadWords(reviewProfane):
    from common import profanityCheck

    result = profanityCheck(reviewProfane)
    assert result["isImpolite"] is True
    assert isinstance(result["badWord"], str)
    assert result["badWord"] != ""


def testProfanityPassesCleanReview(reviewClean):
    from common import profanityCheck

    result = profanityCheck(reviewClean)
    assert result["isImpolite"] is False
    assert result["badWord"] == ""


# sentimentClassify returns label and scores
def testSentimentClassifiesPositive(reviewClean):
    from common import sentimentClassify

    result = sentimentClassify(reviewClean)
    assert result["sentiment"] == "positive"
    assert "sentimentScores" in result
    assert "compound" in result["sentimentScores"]


def testSentimentClassifiesNegative(reviewNegative):
    from common import sentimentClassify

    result = sentimentClassify(reviewNegative)
    assert result["sentiment"] == "negative"


def testSentimentClassifiesNeutral(reviewNeutral):
    from common import sentimentClassify

    result = sentimentClassify(reviewNeutral)
    assert result["sentiment"] == "neutral"


# impolite counter increments per reviewer
def testImpoliteCounterIncrements():
    from common import updateImpoliteCounter, isBanned
    from settings import banThreshold

    reviewer = "A000TESTRPT"
    state: dict = {}  # fresh DynamoDB-like aggregate record

    # three impolite reviews, should not yet ban
    for _ in range(3):
        state = updateImpoliteCounter(reviewer, state, isImpolite=True, threshold=banThreshold)
    assert state["impoliteCount"] == 3
    assert not isBanned(state["impoliteCount"], banThreshold)

    # fourth triggers ban
    state = updateImpoliteCounter(reviewer, state, isImpolite=True, threshold=banThreshold)
    assert state["impoliteCount"] == 4
    assert isBanned(state["impoliteCount"], banThreshold)
    assert state.get("banned") is True


def testImpoliteCounterIgnoresPolite():
    from common import updateImpoliteCounter

    reviewer = "A000TESTPOLITE"
    state: dict = {}
    state = updateImpoliteCounter(reviewer, state, isImpolite=False, threshold=3)
    state = updateImpoliteCounter(reviewer, state, isImpolite=False, threshold=3)
    assert state["impoliteCount"] == 0
    assert state.get("banned") is False


# getInput in direct mode passes event through unchanged
def testGetInputDirectMode():
    from common import getInput

    payload = {"reviewerID": "X", "summary": "test"}
    result = getInput(payload, bucket=None)
    assert result == payload

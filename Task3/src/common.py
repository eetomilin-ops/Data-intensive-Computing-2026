import json
import os
import typing
from urllib.parse import unquote_plus

import boto3

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBClient

# --- boto3 clients (lazy init so functional tests don't need MiniStack) ---
# In Lambda, STAGE=local and MINISTACK_ENDPOINT are set at deploy time.
# Locally, set MINISTACK_ENDPOINT before importing if MiniStack is running.

_s3: "S3Client | None" = None
_ssm: "SSMClient | None" = None
_ddb: "DynamoDBClient | None" = None


def _getS3() -> "S3Client":
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", endpoint_url=_resolveEndpoint())
    return _s3


def _getSsm() -> "SSMClient":
    global _ssm
    if _ssm is None:
        _ssm = boto3.client("ssm", endpoint_url=_resolveEndpoint())
    return _ssm


def _getDdb() -> "DynamoDBClient":
    global _ddb
    if _ddb is None:
        _ddb = boto3.client("dynamodb", endpoint_url=_resolveEndpoint())
    return _ddb


def _resolveEndpoint() -> str | None:
    ep = os.getenv("MINISTACK_ENDPOINT")
    if ep:
        return ep
    # when running with MiniStack test credentials, default to localhost
    if os.getenv("AWS_ACCESS_KEY_ID") == "test":
        return "http://localhost:4566"
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return None  # real Lambda
    return None


# --- NLTK initialisation (module-level: loaded once per Lambda cold start) ---
# Each Lambda invocation no longer re-imports NLTK or rechecks data paths.
# This cuts per-invocation overhead from ~200ms to ~0ms for warm containers.

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer

_lemmatiser = WordNetLemmatizer()
_stopwords: set[str] = set(stopwords.words("english"))
_sia = SentimentIntensityAnalyzer()

def _initNltk():
    # SSM for Lambda bundled data; local dev falls back to default NLTK data dir
    try:
        nltkDataPath = getSsmParam("/review-app/nltk/data-path")
    except Exception:
        nltkDataPath = os.getenv("NLTK_DATA", "")
    if nltkDataPath and os.path.isdir(nltkDataPath):
        nltk.data.path.insert(0, nltkDataPath)
    # minimal downloads if not pre-bundled (local dev fallback)
    for resource in ["punkt_tab", "stopwords", "wordnet", "vader_lexicon"]:
        try:
            nltk.data.find(f"tokenizers/{resource}" if resource == "punkt_tab" else
                           f"corpora/{resource}" if resource in ("stopwords", "wordnet") else
                           f"sentiment/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)

_initNltk()


# --- business logic: preprocessing ---

def preprocess(review: dict) -> dict:
    # combine summary and reviewText into one token stream
    text = f"{review.get('summary', '')} {review.get('reviewText', '')}"
    tokens = word_tokenize(text.lower())

    # keep only alphabetic tokens, drop short tokens, drop stopwords, lemmatise
    clean = []
    for t in tokens:
        if not t.isalpha() or len(t) < 2 or t in _stopwords:
            continue
        # try verb lemma first (e.g. "bought" -> "buy"), fall back to noun
        lemma = _lemmatiser.lemmatize(t, pos='v')
        if lemma == t:
            lemma = _lemmatiser.lemmatize(t)
        clean.append(lemma)

    result = {**review, "tokens": clean}
    return result


# --- business logic: profanity check ---

_profanityFilter = None

def profanityCheck(review: dict) -> dict:
    global _profanityFilter
    if _profanityFilter is None:
        from profanityfilter import ProfanityFilter
        _profanityFilter = ProfanityFilter()

    text = f"{review.get('summary', '')} {review.get('reviewText', '')}"
    # chunk long texts to avoid regex timeout; first profane chunk exits with
    # a marker word -- the flag drives the counter, the marker is for logging
    chunkSize = 2000
    for i in range(0, len(text), chunkSize):
        chunk = text[i:i + chunkSize]
        if _profanityFilter.is_profane(chunk):
            return {**review, "isImpolite": True, "badWord": "profane"}
    return {**review, "isImpolite": False, "badWord": ""}


# --- business logic: sentiment classification ---

def sentimentClassify(review: dict) -> dict:
    text = f"{review.get('summary', '')} {review.get('reviewText', '')}"
    # NLTK VADER uses snake_case API (third-party lib)
    scores = _sia.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    result = {**review, "sentiment": label, "sentimentScores": scores}
    return result


# --- business logic: impolite counter + ban rule ---

def updateImpoliteCounter(
    reviewerID: str,
    state: dict,
    isImpolite: bool = False,
    threshold: int | None = None,            # if None, read from SSM at runtime
) -> dict:
    count = state.get("impoliteCount", 0)
    if isImpolite:
        count += 1
    state["impoliteCount"] = count
    if threshold is None:
        threshold = int(getSsmParam("/review-app/ban/threshold"))
    state["banned"] = isBanned(count, threshold)
    return state


def isBanned(counter: int, threshold: int) -> bool:
    return counter > threshold


# --- transport layer: getInput ---

def getInput(
    event: dict,
    bucket: str | None = None,          # S3 bucket to read from; None or non-S3-event = direct
) -> dict:
    # if event is not an S3 ObjectCreated notification, treat as direct payload
    records = event.get("Records")
    if not records or not isinstance(records, list) or len(records) == 0:
        return event
    rec = records[0]
    if "s3" not in rec:
        return event
    if not bucket:
        return event

    srcBucket = rec["s3"]["bucket"]["name"]
    srcKey = unquote_plus(rec["s3"]["object"]["key"])
    resp = _getS3().get_object(Bucket=srcBucket, Key=srcKey)
    body = resp["Body"].read().decode("utf-8")
    return json.loads(body)


# --- transport layer: sendOutput ---

def sendOutput(
    result: dict,
    bucket: str | None = None,           # S3 bucket to upload to
) -> None:
    if not result.get('reviewerID') or not bucket: # skip records without reviewerID, it poisons lambdas
        return
    payload = json.dumps(result)
    key = f"{result['reviewerID']}_{result.get('asin', '0')}.json"
    _getS3().put_object(Bucket=bucket, Key=key, Body=payload)


# --- DynamoDB helpers ---

def getSsmParam(name: str) -> str:
    resp = _getSsm().get_parameter(Name=name)
    return resp["Parameter"]["Value"]


def writeReviewToDdb(table: str, review: dict):
    item: dict = {
        "reviewerID": {"S": review["reviewerID"]},
        "asin": {"S": review.get("asin", "")},
        "sentiment": {"S": review.get("sentiment", "")},
        "isImpolite": {"BOOL": review.get("isImpolite", False)},
    }
    # DynamoDB SS rejects empty lists and duplicates -- deduplicate before storing
    if review.get("badWord"):
        item["badWord"] = {"S": review["badWord"]}
    if review.get("tokens"):
        uniqueTokens = list(dict.fromkeys(review["tokens"]))  # preserves order, drops dupes
        item["tokens"] = {"SS": uniqueTokens}
    _getDdb().put_item(TableName=table, Item=item)


# Extract INSERT/MODIFY records from a DynamoDB Stream event batch.
# Each record is a type-tagged DynamoDB item; this strips the type wrappers
# and returns plain Python dicts keyed by attribute name.
def parseDdbStream(event: dict) -> list[dict]:
    records = []
    for rec in event.get("Records", []):  # events are coming in batches by 10, see --batch-size for MiniStack
        if rec.get("eventName") in ("INSERT", "MODIFY"):
            raw = rec.get("dynamodb", {}).get("NewImage", {})
            item = {}
            for k, v in raw.items(): # I will  not use map for 4 attributes
                if "S" in v:
                    item[k] = v["S"]
                elif "N" in v:
                    item[k] = int(v["N"]) if v["N"].isdigit() else float(v["N"])
                elif "BOOL" in v:
                    item[k] = v["BOOL"]
                elif "SS" in v:
                    item[k] = list(v["SS"])
            records.append(item)
    return records

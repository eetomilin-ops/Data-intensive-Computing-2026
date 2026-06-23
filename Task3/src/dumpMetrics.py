# Dump computed metrics from DynamoDB to data/output.csv.
# Reads reviewsTable (sentiment + profanity counts) and aggregatesTable (bans).
# Called by runMe.sh after the pipeline has processed reviews_devset.json.

import csv
import os
import sys

import boto3

# endpoint auto-detection: MiniStack test creds -> localhost, else env var
_endpoint = os.getenv("MINISTACK_ENDPOINT")
if not _endpoint and os.getenv("AWS_ACCESS_KEY_ID") == "test":
    _endpoint = "http://localhost:4566"

ddb = boto3.client("dynamodb", endpoint_url=_endpoint)
ssm = boto3.client("ssm", endpoint_url=_endpoint)


def scanAll(table: str) -> list[dict]:
    items: list[dict] = []
    kwargs: dict = {"TableName": table}
    while True:
        resp = ddb.scan(**kwargs)
        items.extend(resp.get("Items", []))
        startKey = resp.get("LastEvaluatedKey")
        if not startKey:
            break
        kwargs["ExclusiveStartKey"] = startKey
    return items


def main():
    reviewsTable = ssm.get_parameter(Name="/review-app/tables/reviews")["Parameter"]["Value"]
    aggTable = ssm.get_parameter(Name="/review-app/tables/aggregates")["Parameter"]["Value"]

    print(f"Scanning {reviewsTable} ...")
    reviews = scanAll(reviewsTable)

    positive = neutral = negative = profanityFails = 0
    userPositive = userNeutral = userNegative = 0
    for item in reviews:
        sentiment = item.get("sentiment", {}).get("S", "")
        isImpolite = item.get("isImpolite", {}).get("BOOL", False)
        userSentiment = item.get("userSentiment", {}).get("S", "")
        if sentiment == "positive":
            positive += 1
        elif sentiment == "negative":
            negative += 1
        else:
            neutral += 1
        if isImpolite:
            profanityFails += 1
        if userSentiment == "positive":
            userPositive += 1
        elif userSentiment == "negative":
            userNegative += 1
        else:
            userNeutral += 1

    print(f"Scanning {aggTable} ...")
    aggregates = scanAll(aggTable)
    bannedUsers = [item["reviewerID"]["S"] for item in aggregates if item.get("banned", {}).get("BOOL") is True]
    bannedUsers.sort()

    # determine output path relative to workspace root
    outDir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(outDir, exist_ok=True)
    outPath = os.path.join(outDir, "output.csv")

    with open(outPath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["positive_reviews", positive])
        w.writerow(["neutral_reviews", neutral])
        w.writerow(["negative_reviews", negative])
        w.writerow(["profanity_failures", profanityFails])
        w.writerow(["banned_users", len(bannedUsers)])
        w.writerow(["banned_user_ids", ", ".join(bannedUsers)])
        w.writerow(["user_positive_reviews", userPositive])
        w.writerow(["user_neutral_reviews", userNeutral])
        w.writerow(["user_negative_reviews", userNegative])

    print(f"Wrote {outPath}")
    print(f"  positive={positive} neutral={neutral} negative={negative}")
    print(f"  user_positive={userPositive} user_neutral={userNeutral} user_negative={userNegative}")
    print(f"  profanity_failures={profanityFails}")
    print(f"  banned_users={len(bannedUsers)} [{', '.join(bannedUsers[:10])}{'...' if len(bannedUsers) > 10 else ''}]")


if __name__ == "__main__":
    main()

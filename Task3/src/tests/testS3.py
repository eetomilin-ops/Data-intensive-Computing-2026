import json
import time
import typing
import uuid

import pytest

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_dynamodb import DynamoDBClient


# --- Lambda readiness waiter (matches sample pattern) ---

@pytest.fixture(autouse=True)
def _waitForLambdas(lambdaClient: "LambdaClient"):
    # block until deployed Lambdas are active before running any integration test
    for fn in ["preprocessing", "profanity", "sentiment", "reducer"]:
        try:
            lambdaClient.get_waiter("function_active").wait(FunctionName=fn)
        except Exception:
            pass  # not deployed yet -- tests that need them will skip


# --- S3 transport test (needs MiniStack, no Lambdas) ---

def testGetInputS3Mode(s3Client: "S3Client"):
    from common import getInput

    testBucket = "test-input-bucket"
    testKey = "unit-test-review.json"
    s3Client.create_bucket(Bucket=testBucket)
    s3Client.put_object(Bucket=testBucket, Key=testKey,
                        Body=json.dumps({"reviewerID": "S3TEST", "summary": "from s3"}))

    s3Event = {
        "Records": [{
            "s3": {
                "bucket": {"name": testBucket},
                "object": {"key": testKey},
            }
        }]
    }
    result = getInput(s3Event, bucket=testBucket)
    assert result["reviewerID"] == "S3TEST"
    assert result["summary"] == "from s3"

    # cleanup
    s3Client.delete_object(Bucket=testBucket, Key=testKey)
    s3Client.delete_bucket(Bucket=testBucket)


# --- full-pipeline integration tests (require MiniStack + deployed resources) ---

@pytest.mark.integration
class TestFullPipeline:
    """End-to-end tests that exercise deployed Lambdas on MiniStack.

    Run only after runMe.sh --deployS3 has created all resources:
        pytest Task3/src/tests/testS3.py -m integration -v
    """

    @pytest.fixture(autouse=True)
    def _setup(self, ssmClient: "SSMClient"):
        self.ssmClient = ssmClient
        # read resource names from SSM (pushed by runMe.sh --deployS3)
        try:
            self.inputBucket = ssmClient.get_parameter(
                Name="/review-app/buckets/input"
            )["Parameter"]["Value"]
            self.reviewsTable = ssmClient.get_parameter(
                Name="/review-app/tables/reviews"
            )["Parameter"]["Value"]
            self.aggTable = ssmClient.get_parameter(
                Name="/review-app/tables/aggregates"
            )["Parameter"]["Value"]
        except Exception:
            pytest.skip("SSM parameters not found -- run runMe.sh --deployS3 first")

    def testPreprocessingLambdaWritesToS3(self, s3Client: "S3Client"):
        """Upload a review to input bucket, verify preprocessing output in staging bucket."""
        reviewer = f"PRETEST-{uuid.uuid4().hex[:8]}"
        review = {
            "reviewerID": reviewer,
            "asin": "B00PRETEST1",
            "summary": "Excellent device",
            "reviewText": "Works perfectly and the build quality is amazing.",
            "overall": 5.0,
        }
        key = f"{reviewer}.json"
        s3Client.put_object(Bucket=self.inputBucket, Key=key,
                            Body=json.dumps(review))

        # preprocessing outputs with key = reviewerID_asin.json (set by sendOutput)
        outKey = f"{reviewer}_{review['asin']}.json"
        stagingBucket = self.ssmClient.get_parameter(
            Name="/review-app/buckets/staging-profanity"
        )["Parameter"]["Value"]

        deadline = time.time() + 15
        found = None
        while time.time() < deadline:
            try:
                resp = s3Client.get_object(Bucket=stagingBucket, Key=outKey)
                found = json.loads(resp["Body"].read())
                break
            except Exception:
                time.sleep(0.5)

        assert found is not None, "preprocessed result not found in staging bucket"
        assert "tokens" in found
        assert len(found["tokens"]) > 0

        # cleanup
        s3Client.delete_object(Bucket=self.inputBucket, Key=key)
        s3Client.delete_object(Bucket=stagingBucket, Key=outKey)

    def testFullChainS3Mode(self, s3Client: "S3Client",
                              ddbClient: "DynamoDBClient"):
        """Upload a review to S3 input bucket, wait for DynamoDB result."""
        reviewer = f"INTTEST-{uuid.uuid4().hex[:8]}"
        review = {
            "reviewerID": reviewer,
            "asin": "B00INTEGR02",
            "summary": "Pretty good item",
            "reviewText": "I enjoyed using this product. It met my expectations.",
            "overall": 4.0,
        }
        key = f"{reviewer}.json"

        s3Client.put_object(Bucket=self.inputBucket, Key=key,
                            Body=json.dumps(review))

        # poll DynamoDB for the processed record (chain: preprocess -> profanity -> sentiment -> ddb)
        result = None
        deadline = time.time() + 30
        while time.time() < deadline:
            resp = ddbClient.get_item(
                TableName=self.reviewsTable,
                Key={"reviewerID": {"S": reviewer}, "asin": {"S": review["asin"]}},
            )
            if "Item" in resp:
                result = resp["Item"]
                break
            time.sleep(0.5)

        assert result is not None, "review not found in DynamoDB after 30s"
        assert result["sentiment"]["S"] == "positive"
        assert result["isImpolite"]["BOOL"] is False
        assert len(result["tokens"]["SS"]) > 0

        # cleanup
        s3Client.delete_object(Bucket=self.inputBucket, Key=key)
        ddbClient.delete_item(TableName=self.reviewsTable,
                              Key={"reviewerID": {"S": reviewer}, "asin": {"S": review["asin"]}})

    def testBanRulePersisted(self, s3Client: "S3Client",
                               ddbClient: "DynamoDBClient"):
        """Upload 4 impolite reviews from same reviewer, assert ban flag."""
        reviewer = f"BANTEST-{uuid.uuid4().hex[:8]}"

        for n in range(4):
            review = {
                "reviewerID": reviewer,
                "asin": f"B00BAN{n:04d}",
                "summary": "Total garbage crap",
                "reviewText": "This damn thing is worthless. The seller is an idiot.",
                "overall": 1.0,
            }
            key = f"{reviewer}_{n}.json"
            s3Client.put_object(Bucket=self.inputBucket, Key=key,
                                Body=json.dumps(review))

        # poll aggregatesTable for the ban flag
        state = None
        deadline = time.time() + 60
        while time.time() < deadline:
            resp = ddbClient.get_item(
                TableName=self.aggTable,
                Key={"reviewerID": {"S": reviewer}},
            )
            item = resp.get("Item", {})
            if item.get("banned", {}).get("BOOL") is True:
                state = item
                break
            time.sleep(0.5)

        assert state is not None, "ban flag not set in aggregatesTable after 60s"
        assert int(state["impoliteCount"]["N"]) >= 4
        assert state["banned"]["BOOL"] is True

        # cleanup S3
        for n in range(4):
            s3Client.delete_object(Bucket=self.inputBucket,
                                   Key=f"{reviewer}_{n}.json")
        # cleanup DynamoDB
        ddbClient.delete_item(TableName=self.aggTable,
                              Key={"reviewerID": {"S": reviewer}})

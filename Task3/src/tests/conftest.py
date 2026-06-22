import json
import os
import sys
import typing
from pathlib import Path

# ensure bare imports from settings/common work both in Lambda and local pytest
_srcDir = Path(__file__).resolve().parent.parent
if str(_srcDir) not in sys.path:
    sys.path.insert(0, str(_srcDir))

import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: test requires MiniStack running")

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_dynamodb import DynamoDBClient

# --- boto3 clients for integration tests (MiniStack must be up) ---

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

ministackUrl = os.environ.get("MINISTACK_ENDPOINT", "http://localhost:4566")

testDataDir = Path(__file__).resolve().parent / "data"


def loadTestJson(name: str) -> dict:
    with open(testDataDir / f"{name}.json") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def s3Client() -> "S3Client":
    import boto3
    return boto3.client("s3", endpoint_url=ministackUrl)


@pytest.fixture(scope="session")
def ssmClient() -> "SSMClient":
    import boto3
    return boto3.client("ssm", endpoint_url=ministackUrl)


@pytest.fixture(scope="session")
def lambdaClient() -> "LambdaClient":
    import boto3
    return boto3.client("lambda", endpoint_url=ministackUrl)


@pytest.fixture(scope="session")
def ddbClient() -> "DynamoDBClient":
    import boto3
    return boto3.client("dynamodb", endpoint_url=ministackUrl)


# --- test review fixtures (loaded from data/*.json) ---

@pytest.fixture
def reviewClean() -> dict:
    return loadTestJson("reviewClean")


@pytest.fixture
def reviewProfane() -> dict:
    return loadTestJson("reviewProfane")


@pytest.fixture
def reviewNegative() -> dict:
    return loadTestJson("reviewNegative")


@pytest.fixture
def reviewNeutral() -> dict:
    return loadTestJson("reviewNeutral")

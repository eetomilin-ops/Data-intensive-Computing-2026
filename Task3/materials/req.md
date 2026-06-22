# Assignment 3 -- Serverless Review Analysis

## Project  goal
Implement an **event-driven serverless application** to perform **profanity check** and **sentiment analysis** of customer reviews. The focus is on design and implementation of a serverless application, not on application KPIs (e.g.processing time, accuracy).

## Environment
- **MiniStack** (AWS emulator) already set up on the LBD cluster.
- Can also run MiniStack locally.
- Local MiniStack is **ephemeral** -- restarting it requires recreating ALL resources
  (S3 buckets, DynamoDB tables, Lambda functions, etc.).


## Core tasks (function chain)

| Step | Description |
|------|-------------|
| 1. Preprocessing | Tokenization, stop-word removal, lemmatization of `summary` and `reviewText` |
| 2. Profanity check | Detect presence of bad words in the review |
| 3. Sentiment analysis | Classify review sentiment (positive / neutral / negative) |
| 4. Impolite counter | Count number of impolite reviews (containing bad words) per customer |
| 5. Ban rule | Mark a customer as banned when they have inserted **more than 3** impolite reviews |

---

## Task requirements

### Lambda Functions (minimum 3)
1. **preprocessing** -- tokenize, remove stopwords, lemmatize
2. **profanity-check** -- detect bad words
3. **sentiment-analysis** -- classify sentiment

### Trigger Chain
- Chain **starts** when a new, single review JSON object is inserted into an **S3 bucket**.
- Subsequent function invocations MUST be triggered by **S3 bucket events**
  and/or **DynamoDB events** (ObjectCreated, item inserted, etc.).

### Data Fields
For each review the following fields must be considered:
- `summary`
- `reviewText`
- `overall`

### SSM Parameter Store
Bucket names, table names, and other configuration parameters MUST be retrieved
from the **SSM Parameter Store** (see tutorial lambdas for pattern).

### Integration Tests
Automated integration tests (pytest) must verify the main functionalities:
- Preprocessing
- Profanity check
- Sentiment analysis
- Counting impolite reviews
- Banning a user

See `projectSample/tests/test_integration.py` for a starting point.

---

## Dataset
- `reviews_devset.json` (same dataset used in earlier assignments).
- Additional custom reviews for corner-case testing are allowed; include them in
  the submission archive.

---

## Results to Report
1. Number of **positive**, **neutral**, and **negative** reviews in `reviews_devset.json`
2. Number of reviews that **failed the profanity check**
3. Users resulting in a **ban** (if any)

Results must be based ONLY on `reviews_devset.json`, not on custom test reviews.

---

## Report (`report.pdf`)
Max **8 pages**, **11pt font**, **one-column** format. At least 5 sections:
1. Introduction
2. Problem Overview
3. Methodology and Approach
4. Results
5. Conclusions

Must include an **architectural diagram** showing:
- The function chain
- How functions interact with PaaS services (S3, DynamoDB, etc.)
- What the trigger events are


```
A demo notebook is available at `dataLAB/demos/ministack_demo.ipynb`.

### Python Packages
- **NLTK** (Natural Language Toolkit) -- preprocessing and sentiment analysis
- **profanityfilter** -- profanity check

### Triggering Multiple Functions from One Event
Use **EventBridge** or **SNS**. Example with EventBridge:
1. Enable S3 bucket events to EventBridge:
   ```bash
   aws s3api put-bucket-notification-configuration \
     --bucket YOUR_BUCKET_NAME \
     --notification-configuration '{"EventBridgeConfiguration": {}}'
   ```
2. Create an EventBridge rule with an event pattern matching S3 ObjectCreated events.
3. Attach multiple Lambda functions as targets to the rule.

### Updating Function Code
```bash
aws lambda update-function-code \
  --function-name YOUR_FUNCTION_NAME \
  --zip-file fileb://YOUR_FUNCTION_ZIP.zip
```

### Delete a Function
```bash
aws lambda delete-function --function-name YOUR_FUNCTION_NAME
```

### S3 File Operations
```bash
aws s3 cp YOUR_FILEPATH s3://YOUR_BUCKET_NAME          # upload
aws s3 cp s3://YOUR_BUCKET_NAME/YOUR_FILEPATH .         # download
```

### Adding Python Packages to Lambda ZIP
Install packages into the ZIP archive (as done for the Resizer Lambda in the
tutorial). See: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
**Max unzipped archive size: 250 MB.**

### Adding Resources (e.g. NLTK data)
Pre-download required NLTK corpora/tokenizers and include them in the Lambda ZIP
archive so they are available at runtime without network access.

### Debugging
- MiniStack runs in debug mode -- check console logs.
- Health check: `http://localhost:4566/health`

---

## Identified Stack & Versions

| Component | Version / Notes |
|-----------|----------------|
| **Python** | **3.12.x** (project `.venv` is 3.12.13; Lambda on MiniStack uses 3.11, but LBD cluster target is 3.12 per workspace instructions) |
| **MiniStack** | Latest (pre-installed on LBD cluster, `ministack` command) |
| **boto3** | AWS SDK for Python (version TBD -- use latest compatible) |
| **NLTK** | Natural Language Toolkit -- preprocessing (tokenize, stopwords, lemmatize) + sentiment analysis (VADER) |
| **profanityfilter** | Profanity / bad-word detection |
| **pytest** | Integration testing |
| **awscli** | AWS CLI for resource management scripts |
| **mypy-boto3-s3** | Type stubs for boto3 S3 (dev only, optional) |
| **mypy-boto3-ssm** | Type stubs for boto3 SSM (dev only, optional) |
| **mypy-boto3-lambda** | Type stubs for boto3 Lambda (dev only, optional) |
| **mypy-boto3-dynamodb** | Type stubs for boto3 DynamoDB (dev only, optional) |
| **black** | Code formatter (dev only, optional) |

### AWS Services Used
- **S3** -- review storage, event triggers
- **DynamoDB** -- customer state (impolite counters, ban flags), event triggers
- **Lambda** -- function compute (Python 3.11 runtime on MiniStack)
- **SSM Parameter Store** -- configuration (bucket names, table names)
- **EventBridge** (or SNS) -- fan-out S3 events to multiple Lambdas

### Python Version Note
The project `.venv` already uses **Python 3.12.13**. Lambda functions on
MiniStack are configured with `python3.11` runtime (see `run.sh`). This is fine:
the Lambda runtime is independent from the local venv. Keep the local venv at
**3.12** for development and testing, matching the workspace target.


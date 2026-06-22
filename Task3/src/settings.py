# --- AWS / MiniStack connection (used by pushSettings.sh and common.py) ---
# Kept in this file rather than a global env var so redeployment across
# different environments (local MiniStack vs LBD cluster proxy) is
# explicit -- change the value here, push to SSM, and Lambdas pick it up.
awsAccessKeyId = "test"
awsSecretAccessKey = "test"
awsRegion = "us-east-1"
# overridable via env var for cluster proxy: MINISTACK_ENDPOINT
ministackEndpoint = __import__("os").environ.get("MINISTACK_ENDPOINT", "http://localhost:4566")

# --- SSM parameter prefix ---
ssmPrefix = "/review-app"

# --- S3 bucket names ---
bucketInput = "review-app-input"
bucketStagingProfanity = "review-app-staging-profanity"
bucketStagingSentiment = "review-app-staging-sentiment"

# --- DynamoDB table names ---
tableReviews = "reviewsTable"
tableAggregates = "aggregatesTable"
tableErrors = "errorsTable"

# --- Ban threshold: more than this many impolite reviews triggers a ban ---
banThreshold = 3

# --- Lambda function names ---
functionPreprocessing = "preprocessing"
functionProfanity = "profanity"
functionSentiment = "sentiment"
functionReducer = "reducer"

# --- Lambda runtime config ---
lambdaRuntime = "python3.11"
lambdaTimeout = 60
lambdaMemory = 256
# max concurrent invocations per Lambda (S3 events queue beyond this)
# 5 selected: 4 Lambdas * 5 = 20 threads, well within macOS 5,568 limit
# keeps CPU/memory load low while processing ~15 reviews/sec
lambdaConcurrency = 5

# --- NLTK data path inside Lambda ZIP ---
# Bundled at /opt/nltk_data; set NLTK_DATA env var on each Lambda
nltkDataPath = "/opt/nltk_data"

# --- Pipeline throttle ---
# Fraction of uploaded reviews that must land in DDB before the next S3 batch
# is sent. 0.9 gives MiniStack's S3-event threads time to drain, preventing
# "can't start new thread" explosions from event-thread fan-out.
pipelineBatchThreshold = 0.9

def handler(event, context):
    try:
        from common import getInput, sentimentClassify, writeReviewToDdb, getSsmParam

        bucketIn = getSsmParam("/review-app/buckets/staging-sentiment")
        table = getSsmParam("/review-app/tables/reviews")

        review = getInput(event, bucket=bucketIn or None)
        result = sentimentClassify(review)
        writeReviewToDdb(table, result)
        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "errorMessage": str(e)}

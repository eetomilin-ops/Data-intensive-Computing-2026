def handler(event, context):
    try:
        from common import getInput, sendOutput, profanityCheck, getSsmParam

        bucketIn = getSsmParam("/review-app/buckets/staging-profanity")
        bucketOut = getSsmParam("/review-app/buckets/staging-sentiment")

        review = getInput(event, bucket=bucketIn or None)
        result = profanityCheck(review)
        sendOutput(result, bucket=bucketOut or None)
        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "errorMessage": str(e)}

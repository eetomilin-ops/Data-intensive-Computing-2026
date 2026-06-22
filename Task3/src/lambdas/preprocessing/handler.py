def handler(event, context):
    try:
        from common import getInput, sendOutput, preprocess, getSsmParam

        bucketIn = getSsmParam("/review-app/buckets/input")
        bucketOut = getSsmParam("/review-app/buckets/staging-profanity")

        review = getInput(event, bucket=bucketIn or None)
        result = preprocess(review)
        sendOutput(result, bucket=bucketOut or None)
        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "errorMessage": str(e)}

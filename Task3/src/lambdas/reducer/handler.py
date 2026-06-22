def handler(event, context):
    try:
        from common import parseDdbStream, updateImpoliteCounter, getSsmParam, _getDdb

        aggTable = getSsmParam("/review-app/tables/aggregates")
        errTable = getSsmParam("/review-app/tables/errors")
        banThreshold = int(getSsmParam("/review-app/ban/threshold"))
        import uuid, traceback, json
        ddbClient = _getDdb()

        for record in parseDdbStream(event):
            reviewerID = record.get("reviewerID")
            isImpolite = record.get("isImpolite", False)
            if not reviewerID:
                continue

            try:
                resp = ddbClient.get_item(
                    TableName=aggTable,
                    Key={"reviewerID": {"S": reviewerID}},
                )
                item = resp.get("Item", {})
                state = {
                    "impoliteCount": int(item.get("impoliteCount", {}).get("N", 0)),
                    "banned": item.get("banned", {}).get("BOOL", False),
                }

                state = updateImpoliteCounter(reviewerID, state, isImpolite=isImpolite, threshold=banThreshold)

                ddbClient.put_item(
                    TableName=aggTable,
                    Item={
                        "reviewerID": {"S": reviewerID},
                        "impoliteCount": {"N": str(state["impoliteCount"])},
                        "banned": {"BOOL": state.get("banned", False)},
                    },
                )
            except Exception:
                ddbClient.put_item(
                    TableName=errTable,
                    Item={
                        "errorID": {"S": str(uuid.uuid4())},
                        "reviewerID": {"S": reviewerID},
                        "message": {"S": traceback.format_exc()},
                        "payload": {"S": json.dumps(record)},
                    },
                )

        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "errorMessage": str(e)}

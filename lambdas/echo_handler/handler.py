import json


def lambda_handler(event, context):
    raw_body = event.get("body") or "{}"

    try:
        body = json.loads(raw_body)
    except (TypeError, ValueError):
        body = raw_body

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }

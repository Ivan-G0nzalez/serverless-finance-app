import json
import os
import boto3

from telegram import parse_update

lambda_client = boto3.client("lambda")
FINANCE_PROCESSOR_ARN = os.environ["FINANCE_PROCESSOR_ARN"]


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    parsed = parse_update(body)
    if not parsed:
        return {"statusCode": 200, "body": "ok"}

    # Invocación async — Telegram espera respuesta en < 5s
    lambda_client.invoke(
        FunctionName=FINANCE_PROCESSOR_ARN,
        InvocationType="Event",
        Payload=json.dumps(parsed).encode(),
    )

    return {"statusCode": 200, "body": "ok"}

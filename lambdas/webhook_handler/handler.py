import json
import os
import boto3

from telegram import parse_update, send_message

lambda_client = boto3.client("lambda")
FINANCE_PROCESSOR_ARN = os.environ["FINANCE_PROCESSOR_ARN"]


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    parsed = parse_update(body)
    if not parsed:
        return {"statusCode": 200, "body": "ok"}

    chat_id, user_id, text = parsed

    # Invocación async — Telegram espera respuesta en < 5s
    lambda_client.invoke(
        FunctionName=FINANCE_PROCESSOR_ARN,
        InvocationType="Event",
        Payload=json.dumps({
            "chat_id": chat_id,
            "user_id": user_id,
            "text": text,
        }).encode(),
    )

    return {"statusCode": 200, "body": "ok"}

"""
Registra el webhook de Telegram apuntando al API Gateway.

Uso:
    python scripts/set_webhook.py <API_GATEWAY_URL>

El API_GATEWAY_URL lo obtienes del output de terraform apply:
    terraform -chdir=terraform output api_gateway_url
"""
import sys
import json
import urllib.request
import urllib.parse
import os


def main():
    if len(sys.argv) < 2:
        print("Uso: python set_webhook.py <API_GATEWAY_URL>")
        sys.exit(1)

    webhook_url = sys.argv[1].rstrip("/")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: define la variable de entorno TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = json.dumps({"url": webhook_url}).encode()
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if result.get("ok"):
        print(f"✅ Webhook registrado en: {webhook_url}")
    else:
        print(f"❌ Error: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()

import json
import os
import urllib.request


TELEGRAM_API = "https://api.telegram.org/bot{}".format(os.environ["TELEGRAM_BOT_TOKEN"])


def send_message(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(
        f"{TELEGRAM_API}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)


def parse_update(body: dict) -> tuple[int, int, str] | None:
    """Extrae (chat_id, user_id, texto) del update de Telegram. Retorna None si no es mensaje de texto."""
    message = body.get("message") or body.get("edited_message")
    if not message:
        return None
    text = message.get("text")
    if not text:
        return None
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    return chat_id, user_id, text

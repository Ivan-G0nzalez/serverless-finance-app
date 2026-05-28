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


def parse_update(body: dict) -> dict | None:
    """Extrae datos del update de Telegram. Soporta mensajes de texto y de voz."""
    message = body.get("message") or body.get("edited_message")
    if not message:
        return None
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    if text := message.get("text"):
        return {"chat_id": chat_id, "user_id": user_id, "text": text}
    if voice := message.get("voice"):
        return {"chat_id": chat_id, "user_id": user_id, "voice_file_id": voice["file_id"]}
    return None

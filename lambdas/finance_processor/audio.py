import io
import json
import os
import urllib.request

from openai import OpenAI

TELEGRAM_API = "https://api.telegram.org/bot{}".format(os.environ["TELEGRAM_BOT_TOKEN"])
_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def transcribe_voice(file_id: str) -> str:
    url = f"{TELEGRAM_API}/getFile?file_id={file_id}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    file_path = data["result"]["file_path"]

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    with urllib.request.urlopen(download_url) as resp:
        audio_bytes = resp.read()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice.ogg"

    transcription = _client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="es",
    )
    return transcription.text

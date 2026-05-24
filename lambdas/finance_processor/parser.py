import json
import os
import anthropic

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """Eres un asistente de finanzas personales.
El usuario te enviará mensajes en lenguaje natural sobre sus gastos e ingresos.

Debes responder ÚNICAMENTE con un JSON válido con la siguiente estructura:

Para un gasto:
{"action": "gasto", "monto": <número>, "categoria": "<gastos|lujos|regalos>", "descripcion": "<descripción breve>"}

Para un ingreso:
{"action": "ingreso", "monto": <número>, "descripcion": "<descripción breve>"}

Para consulta de balance:
{"action": "balance"}

Si el mensaje no es sobre finanzas o no lo entiendes:
{"action": "desconocido", "mensaje": "<respuesta amigable para el usuario>"}

Reglas de categorización:
- gastos: necesidades del día a día (comida, transporte, servicios, salud)
- lujos: entretenimiento, ropa de marca, restaurantes finos, viajes, tecnología no esencial
- regalos: regalos para otras personas, donaciones

Responde SOLO con el JSON, sin texto adicional."""


def parse_message(text: str) -> dict:
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)

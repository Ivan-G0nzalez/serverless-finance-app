import os
import anthropic

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """Eres un asistente de finanzas personales.
El usuario te enviará mensajes en lenguaje natural sobre sus gastos e ingresos.

Categorías de gasto:
- gastos: necesidades del día a día (comida, transporte, servicios, salud)
- lujos: entretenimiento, ropa de marca, restaurantes finos, viajes, tecnología no esencial
- regalos: regalos para otras personas, donaciones"""

_TOOLS = [
    {
        "name": "registrar_gasto",
        "description": "Registrar un gasto del usuario. Úsalo cuando el usuario mencione que gastó dinero en algo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monto": {"type": "number", "description": "Cantidad de dinero gastada"},
                "categoria": {
                    "type": "string",
                    "enum": ["gastos", "lujos", "regalos"],
                    "description": "Categoría del gasto",
                },
                "descripcion": {"type": "string", "description": "Descripción breve del gasto"},
            },
            "required": ["monto", "categoria", "descripcion"],
        },
    },
    {
        "name": "registrar_ingreso",
        "description": "Registrar un ingreso del usuario. Úsalo cuando el usuario mencione que recibió dinero.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monto": {"type": "number", "description": "Cantidad de dinero recibida"},
                "descripcion": {"type": "string", "description": "Descripción breve del ingreso"},
            },
            "required": ["monto", "descripcion"],
        },
    },
    {
        "name": "consultar_balance",
        "description": "Consultar el balance del usuario. Úsalo cuando pregunte por su balance, cuánto ha gastado o cuánto tiene.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "mensaje_desconocido",
        "description": "Úsalo cuando el mensaje no esté relacionado con finanzas o no se pueda clasificar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mensaje": {"type": "string", "description": "Respuesta amigable para el usuario"},
            },
            "required": ["mensaje"],
        },
    },
]

_ACTION_MAP = {
    "registrar_gasto": "gasto",
    "registrar_ingreso": "ingreso",
    "consultar_balance": "balance",
    "mensaje_desconocido": "desconocido",
}


def parse_message(text: str) -> dict:
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        tools=_TOOLS,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": text}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return {"action": _ACTION_MAP[tool_use.name], **tool_use.input}

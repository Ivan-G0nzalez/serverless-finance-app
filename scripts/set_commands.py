"""
Registra los comandos del bot en Telegram para que aparezcan como sugerencias al escribir /.

Uso:
    python scripts/set_commands.py

Requiere la variable de entorno TELEGRAM_BOT_TOKEN.
"""
import json
import os
import sys
import urllib.request

COMMANDS = [
    {"command": "historial", "description": "Últimas 10 transacciones"},
    {"command": "balance",   "description": "Balance total (ingresos, gastos, neto)"},
    {"command": "hoy",       "description": "Gastos de hoy por categoría"},
    {"command": "semana",    "description": "Gastos de esta semana por categoría"},
    {"command": "mes",       "description": "Gastos del mes en curso por categoría"},
    {"command": "ayuda",     "description": "Lista de todos los comandos disponibles"},
]


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: define la variable de entorno TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    payload = json.dumps({"commands": COMMANDS}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/setMyCommands",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if result.get("ok"):
        print(f"✅ {len(COMMANDS)} comandos registrados en Telegram")
        for cmd in COMMANDS:
            print(f"   /{cmd['command']} — {cmd['description']}")
    else:
        print(f"❌ Error: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()

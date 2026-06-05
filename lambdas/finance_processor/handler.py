import json
import logging
import os
import urllib.request

import audio
import dynamo
import parser as finance_parser
import responses

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TELEGRAM_API = "https://api.telegram.org/bot{}".format(os.environ["TELEGRAM_BOT_TOKEN"])


def _send(chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(
        f"{TELEGRAM_API}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)


def lambda_handler(event, context):
    chat_id: int = event["chat_id"]
    user_id: int = event["user_id"]

    if voice_file_id := event.get("voice_file_id"):
        text = audio.transcribe_voice(voice_file_id)
        logger.info("Transcribed voice from user %s: %s", user_id, text)
    else:
        text = event["text"]

    logger.info("Processing message from user %s: %s", user_id, text)

    try:
        try:
            dynamo.ensure_profile(user_id)
        except Exception:
            pass  # Ya existe el perfil — ConditionalCheckFailedException

        parsed = finance_parser.parse_message(text)
        action = parsed.get("action")

        if action == "gasto":
            monto = float(parsed["monto"])
            categoria = parsed.get("categoria", "gastos")
            descripcion = parsed.get("descripcion", text)
            dynamo.register_transaction(user_id, "gasto", monto, categoria, descripcion)
            reply = responses.gasto_confirmado(monto, categoria, descripcion)

        elif action == "ingreso":
            monto = float(parsed["monto"])
            descripcion = parsed.get("descripcion", text)
            dynamo.register_transaction(user_id, "ingreso", monto, None, descripcion)
            reply = responses.ingreso_confirmado(monto, descripcion)

        elif action == "balance":
            data = dynamo.get_balance(user_id)
            reply = responses.balance_resumen(data)

        elif action == "gastos_periodo":
            data = dynamo.get_period_summary(
                user_id, parsed["fecha_inicio"], parsed["fecha_fin"]
            )
            reply = responses.gastos_periodo(
                data, parsed["descripcion_periodo"], parsed.get("por_categoria", False)
            )

        elif action == "desconocido":
            reply = responses.no_entendido(parsed.get("mensaje", "No entendí tu mensaje."))

        elif action == "listar_transacciones":
            transactions = dynamo.get_recent_transactions(user_id, limit=10)
            reply = responses.lista_transacciones(transactions)

        elif action == "corregir_transaccion":
            numero = int(parsed.get("numero", 0))
            campo = parsed.get("campo", "")
            nuevo_valor_raw = parsed.get("nuevo_valor", "")

            if not (1 <= numero <= 10):
                reply = responses.error_correccion_invalida(f"El número debe estar entre 1 y 10.")
            else:
                transactions = dynamo.get_recent_transactions(user_id, limit=10)
                if numero > len(transactions):
                    reply = responses.error_transaccion_no_encontrada(numero)
                elif campo == "monto":
                    try:
                        nuevo_monto = float(nuevo_valor_raw)
                        if nuevo_monto <= 0:
                            raise ValueError("El monto debe ser positivo.")
                        dynamo.update_transaction(user_id, transactions[numero - 1]["SK"], transactions[numero - 1], campo, nuevo_monto)
                        reply = responses.correccion_confirmada(campo, nuevo_valor_raw, transactions[numero - 1]["descripcion"])
                    except (ValueError, TypeError) as exc:
                        reply = responses.error_correccion_invalida(str(exc))
                elif campo == "categoria":
                    try:
                        dynamo.update_transaction(user_id, transactions[numero - 1]["SK"], transactions[numero - 1], campo, nuevo_valor_raw)
                        reply = responses.correccion_confirmada(campo, nuevo_valor_raw, transactions[numero - 1]["descripcion"])
                    except ValueError as exc:
                        reply = responses.error_correccion_invalida(str(exc))
                else:
                    reply = responses.error_correccion_invalida(f"Campo desconocido: {campo}")

        else:
            reply = responses.no_entendido("No entendí tu mensaje. Puedes decirme algo como: *gasté 200 en comida* o *cuánto tengo de balance*.")

    except Exception as e:
        logger.exception("Error processing message: %s", e)
        reply = responses.error_generico()

    _send(chat_id, reply)
    return {"statusCode": 200}

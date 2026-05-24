import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3

_table = boto3.resource("dynamodb").Table(os.environ["DYNAMODB_TABLE"])

CATEGORIES = ("gastos", "lujos", "regalos")


def _user_pk(user_id: int) -> str:
    return f"USER#{user_id}"


def ensure_profile(user_id: int) -> None:
    pk = _user_pk(user_id)
    _table.put_item(
        Item={"PK": pk, "SK": "PROFILE", "created_at": _now()},
        ConditionExpression="attribute_not_exists(PK)",
    )


def register_transaction(user_id: int, tipo: str, monto: float, categoria: str | None, descripcion: str) -> str:
    pk = _user_pk(user_id)
    ts = datetime.now(timezone.utc).isoformat()
    sk = f"TX#{ts}"

    item = {
        "PK": pk,
        "SK": sk,
        "tipo": tipo,
        "monto": Decimal(str(monto)),
        "descripcion": descripcion,
        "created_at": ts,
    }
    if categoria:
        item["categoria"] = categoria

    _table.put_item(Item=item)
    _update_balance(user_id, tipo, monto, categoria)
    return sk


def _update_balance(user_id: int, tipo: str, monto: float, categoria: str | None) -> None:
    pk = _user_pk(user_id)
    amount = Decimal(str(monto))

    if tipo == "gasto":
        _table.update_item(
            Key={"PK": pk, "SK": "BALANCE#total"},
            UpdateExpression="ADD total_gastos :m SET updated_at = :t",
            ExpressionAttributeValues={":m": amount, ":t": _now()},
        )
        if categoria in CATEGORIES:
            _table.update_item(
                Key={"PK": pk, "SK": f"BALANCE#{categoria}"},
                UpdateExpression="ADD #total :m SET updated_at = :t",
                ExpressionAttributeNames={"#total": "total"},
                ExpressionAttributeValues={":m": amount, ":t": _now()},
            )
    elif tipo == "ingreso":
        _table.update_item(
            Key={"PK": pk, "SK": "BALANCE#total"},
            UpdateExpression="ADD total_ingresos :m SET updated_at = :t",
            ExpressionAttributeValues={":m": amount, ":t": _now()},
        )


def get_balance(user_id: int) -> dict:
    pk = _user_pk(user_id)
    result = _table.get_item(Key={"PK": pk, "SK": "BALANCE#total"}).get("Item", {})

    balances = {}
    for cat in CATEGORIES:
        item = _table.get_item(Key={"PK": pk, "SK": f"BALANCE#{cat}"}).get("Item", {})
        balances[cat] = float(item.get("total", 0))

    ingresos = float(result.get("total_ingresos", 0))
    gastos = float(result.get("total_gastos", 0))

    return {
        "ingresos": ingresos,
        "gastos_total": gastos,
        "neto": ingresos - gastos,
        "por_categoria": balances,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

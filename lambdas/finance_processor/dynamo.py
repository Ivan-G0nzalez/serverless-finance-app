import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

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


def register_transaction(user_id: int, tipo: str, monto: float, categoria: str | None, descripcion: str, medio_de_pago: str = "bancolombia") -> str:
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
    if tipo == "gasto":
        item["medio_de_pago"] = medio_de_pago

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


def get_period_summary(user_id: int, fecha_inicio: str, fecha_fin: str) -> dict:
    pk = _user_pk(user_id)
    items = []
    kwargs = {
        "KeyConditionExpression": Key("PK").eq(pk) & Key("SK").between(
            f"TX#{fecha_inicio}",
            f"TX#{fecha_fin}T23:59:59.999999",
        )
    }
    while True:
        resp = _table.query(**kwargs)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last

    gastos = [i for i in items if i.get("tipo") == "gasto"]
    total = sum(i["monto"] for i in gastos)
    por_categoria = {cat: Decimal("0") for cat in CATEGORIES}
    for i in gastos:
        cat = i.get("categoria")
        if cat in por_categoria:
            por_categoria[cat] += i["monto"]

    return {
        "total": float(total),
        "por_categoria": {k: float(v) for k, v in por_categoria.items()},
        "count": len(gastos),
    }


def get_recent_transactions(user_id: int, limit: int = 10) -> list[dict]:
    pk = _user_pk(user_id)
    resp = _table.query(
        KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with("TX#"),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [
        {
            "SK": item["SK"],
            "tipo": item["tipo"],
            "monto": float(item["monto"]),
            "categoria": item.get("categoria"),
            "descripcion": item.get("descripcion", ""),
            "created_at": item.get("created_at", ""),
            "medio_de_pago": item.get("medio_de_pago"),
        }
        for item in resp.get("Items", [])
    ]


def update_transaction(
    user_id: int,
    sk: str,
    old_item: dict,
    campo: str,
    nuevo_valor: float | str,
) -> None:
    pk = _user_pk(user_id)
    tipo = old_item["tipo"]
    old_monto = Decimal(str(old_item["monto"]))
    old_categoria = old_item.get("categoria")

    if campo == "monto":
        new_monto = Decimal(str(nuevo_valor))
        delta = new_monto - old_monto
        _table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET monto = :m, updated_at = :t",
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeValues={":m": new_monto, ":t": _now()},
        )
        if tipo == "gasto":
            _table.update_item(
                Key={"PK": pk, "SK": "BALANCE#total"},
                UpdateExpression="ADD total_gastos :d SET updated_at = :t",
                ExpressionAttributeValues={":d": delta, ":t": _now()},
            )
            if old_categoria in CATEGORIES:
                _table.update_item(
                    Key={"PK": pk, "SK": f"BALANCE#{old_categoria}"},
                    UpdateExpression="ADD #total :d SET updated_at = :t",
                    ExpressionAttributeNames={"#total": "total"},
                    ExpressionAttributeValues={":d": delta, ":t": _now()},
                )
        elif tipo == "ingreso":
            _table.update_item(
                Key={"PK": pk, "SK": "BALANCE#total"},
                UpdateExpression="ADD total_ingresos :d SET updated_at = :t",
                ExpressionAttributeValues={":d": delta, ":t": _now()},
            )

    elif campo == "categoria":
        if tipo != "gasto":
            raise ValueError("Los ingresos no tienen categoría.")
        new_categoria = str(nuevo_valor)
        if new_categoria not in CATEGORIES:
            raise ValueError(f"Categoría inválida: {new_categoria}. Opciones: {', '.join(CATEGORIES)}")
        if old_categoria == new_categoria:
            return
        _table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET categoria = :c, updated_at = :t",
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeValues={":c": new_categoria, ":t": _now()},
        )
        if old_categoria in CATEGORIES:
            _table.update_item(
                Key={"PK": pk, "SK": f"BALANCE#{old_categoria}"},
                UpdateExpression="ADD #total :d SET updated_at = :t",
                ExpressionAttributeNames={"#total": "total"},
                ExpressionAttributeValues={":d": -old_monto, ":t": _now()},
            )
        _table.update_item(
            Key={"PK": pk, "SK": f"BALANCE#{new_categoria}"},
            UpdateExpression="ADD #total :d SET updated_at = :t",
            ExpressionAttributeNames={"#total": "total"},
            ExpressionAttributeValues={":d": old_monto, ":t": _now()},
        )

    else:
        raise ValueError(f"Campo desconocido: {campo}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

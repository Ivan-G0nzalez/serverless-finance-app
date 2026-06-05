def gasto_confirmado(monto: float, categoria: str, descripcion: str) -> str:
    emoji = {"gastos": "🧾", "lujos": "✨", "regalos": "🎁"}.get(categoria, "💸")
    return f"{emoji} *Gasto registrado*\n💵 ${monto:,.2f} en *{categoria}*\n📝 {descripcion}"


def ingreso_confirmado(monto: float, descripcion: str) -> str:
    return f"💰 *Ingreso registrado*\n💵 ${monto:,.2f}\n📝 {descripcion}"


def balance_resumen(data: dict) -> str:
    cats = data["por_categoria"]
    cat_lines = "\n".join(
        f"  • {cat.capitalize()}: ${v:,.2f}" for cat, v in cats.items()
    )
    signo = "+" if data["neto"] >= 0 else ""
    return (
        f"📊 *Tu balance*\n\n"
        f"💰 Ingresos: ${data['ingresos']:,.2f}\n"
        f"💸 Gastos: ${data['gastos_total']:,.2f}\n"
        f"  {cat_lines}\n\n"
        f"{'🟢' if data['neto'] >= 0 else '🔴'} Neto: {signo}${data['neto']:,.2f}"
    )


def gastos_periodo(data: dict, descripcion_periodo: str, por_categoria: bool = False) -> str:
    if data["count"] == 0:
        return f"📭 No registré gastos en *{descripcion_periodo}*."
    msg = f"📊 *Gastos de {descripcion_periodo}*\n\n💸 Total: ${data['total']:,.2f}"
    if por_categoria:
        lines = "\n".join(
            f"  • {cat.capitalize()}: ${v:,.2f}"
            for cat, v in data["por_categoria"].items()
            if v > 0
        )
        if lines:
            msg += f"\n\n{lines}"
    return msg


def no_entendido(mensaje: str) -> str:
    return f"🤔 {mensaje}"


def lista_transacciones(transactions: list[dict]) -> str:
    if not transactions:
        return "📭 No tienes transacciones registradas aún."
    lines = ["📋 *Tus últimas transacciones:*\n"]
    for i, tx in enumerate(transactions, start=1):
        tipo_emoji = "💸" if tx["tipo"] == "gasto" else "💰"
        cat_str = f" ({tx['categoria']})" if tx.get("categoria") else ""
        fecha = tx.get("created_at", "")[:10]
        lines.append(f"{i}. {tipo_emoji} ${tx['monto']:,.2f}{cat_str} — {tx['descripcion']} _{fecha}_")
    lines.append("\n_Para corregir: 'corrige la #2, el monto era 350' o 'la 3 era categoría lujos'_")
    return "\n".join(lines)


def correccion_confirmada(campo: str, nuevo_valor: str, descripcion: str) -> str:
    if campo == "monto":
        try:
            val = float(nuevo_valor)
            return f"✅ *Corrección aplicada*\n💵 Nuevo monto: ${val:,.2f}\n📝 {descripcion}"
        except ValueError:
            pass
    if campo == "categoria":
        emoji = {"gastos": "🧾", "lujos": "✨", "regalos": "🎁"}.get(nuevo_valor, "📂")
        return f"✅ *Corrección aplicada*\n{emoji} Nueva categoría: *{nuevo_valor}*\n📝 {descripcion}"
    return "✅ Corrección aplicada."


def error_transaccion_no_encontrada(numero: int) -> str:
    return f"⚠️ No encontré la transacción #{numero}. Escribe 'ver mis transacciones' para ver la lista actual."


def error_correccion_invalida(razon: str) -> str:
    return f"⚠️ No se pudo corregir: {razon}"


def error_generico() -> str:
    return "⚠️ Ocurrió un error. Intenta de nuevo en un momento."


def ayuda() -> str:
    return (
        "📖 *Comandos disponibles:*\n\n"
        "• /historial — últimas 10 transacciones\n"
        "• /historial 20 — últimas N (máx 20)\n"
        "• /balance — ingresos, gastos y neto\n"
        "• /hoy — gastos de hoy por categoría\n"
        "• /semana — gastos de esta semana\n"
        "• /mes — gastos de este mes\n\n"
        "_También puedes escribir en lenguaje natural:_\n"
        "_'gasté 200 en comida', 'ingresé 5000', etc._"
    )

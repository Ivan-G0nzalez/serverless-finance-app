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


def no_entendido(mensaje: str) -> str:
    return f"🤔 {mensaje}"


def error_generico() -> str:
    return "⚠️ Ocurrió un error. Intenta de nuevo en un momento."

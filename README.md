# App Finanzas — Telegram Finance Bot on AWS

Bot de Telegram para registrar gastos e ingresos personales. Usa AWS Lambda, DynamoDB y Claude Haiku para clasificar mensajes en lenguaje natural.

---

## Seguridad — Constitución del Repositorio

### Reglas obligatorias

Estas reglas aplican a todos los colaboradores y deben respetarse en todo commit, PR o configuración del proyecto.

**1. Nunca expongas credenciales en el código fuente**
- Tokens de Telegram, API keys de Anthropic, credenciales de AWS y cualquier secreto deben vivir exclusivamente en `terraform/terraform.tfvars` o variables de entorno locales.
- `terraform.tfvars` está en `.gitignore` y **nunca debe commitearse**.
- Usa `.env.example` con valores ficticios como referencia para otros colaboradores.

**2. Nunca hagas hardcode de valores sensibles**
- No incrustar tokens, ARNs con información de cuenta, IDs de cuenta de AWS ni endpoint URLs en código, comentarios o documentación.
- Los valores de entorno se inyectan vía Terraform (`environment_variables` en `lambda.tf`) — no los escribas directamente en los handlers.

**3. Archivos prohibidos en el repositorio**

| Archivo / patrón | Motivo |
|---|---|
| `terraform/terraform.tfvars` | Contiene credenciales reales |
| `.env` | Variables de entorno locales con secretos |
| `terraform/terraform.tfstate` | Puede contener ARNs, IDs y valores de outputs sensibles |
| `terraform/terraform.tfstate.backup` | Idem anterior |
| `builds/*.zip` | Artefactos generados, no pertenecen al repo |

**4. Revisa el diff antes de cada commit**
Antes de hacer `git commit`, ejecuta `git diff --staged` y verifica que no haya ningún valor real de token, key o contraseña en los cambios.

**5. Si accidentalmente expones un secreto**
1. Revoca y rota la credencial de inmediato (Telegram BotFather, Anthropic Console, AWS IAM).
2. Elimina el secreto del historial con `git filter-repo` o contacta al administrador del repositorio.
3. No basta con hacer un nuevo commit que lo borre — el historial de git conserva el valor expuesto.

---

## Arquitectura

```
Telegram → API Gateway → webhook_handler (Lambda)
                              │  InvocationType=Event (async)
                              ▼
                     finance_processor (Lambda)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
               Claude Haiku          DynamoDB
               (parser.py)          (dynamo.py)
                    │
                    ▼
              Telegram API (respuesta al usuario)
```

Dos Lambdas se comunican de forma asíncrona para cumplir el límite de 5 segundos de Telegram sin bloquear mientras Claude procesa el mensaje.

## Variables de Entorno

| Variable | Lambda | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ambas | Token del bot de Telegram |
| `ANTHROPIC_API_KEY` | `finance_processor` | API key de Claude |
| `DYNAMODB_TABLE` | `finance_processor` | Nombre de la tabla (`finanzas`) |
| `FINANCE_PROCESSOR_ARN` | `webhook_handler` | ARN para invocación asíncrona |

## Deploy

```bash
# 1. Instalar dependencias en el layer
pip install -r layers/requirements.txt -t layers/python/

# 2. Copiar y completar variables (nunca commitear este archivo)
cp .env.example terraform/terraform.tfvars

# 3. Desplegar infraestructura
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

# 4. Registrar el webhook de Telegram
TELEGRAM_BOT_TOKEN=<token> python scripts/set_webhook.py $(terraform output -raw api_gateway_url)

# 5. Registrar los comandos slash en Telegram (aparecen como sugerencias al escribir /)
TELEGRAM_BOT_TOKEN=<token> python scripts/set_commands.py
```

## Categorías de Gasto

| Categoría | Descripción |
|---|---|
| `gastos` | Necesidades cotidianas (comida, transporte, salud) |
| `lujos` | Gastos no esenciales (entretenimiento, viajes) |
| `regalos` | Regalos y donaciones |

Para agregar una categoría: actualizar `CATEGORIES` en `dynamo.py` y el system prompt en `parser.py`.

---

## Fase 2 — Roadmap de Mejoras

### Estado actual (Fase 1)

| Capacidad | Implementado |
|---|---|
| Registrar gastos e ingresos por texto | ✅ |
| Mensajes de voz (Whisper) | ✅ |
| Balance acumulado total y por categoría | ✅ |
| Consulta de gastos por período | ✅ |
| Balances atómicos con `ADD` en DynamoDB | ✅ |
| Listar y corregir transacciones (monto/categoría) | ✅ |
| Comandos slash sin LLM (`/historial`, `/balance`, etc.) | ✅ |
| Historial de conversación / contexto multi-turno | ❌ |
| Presupuestos por categoría | ❌ |
| Eliminar transacciones | ❌ |
| Dashboard web | ❌ |
| Notificaciones proactivas | ❌ |

---

### Alta prioridad

#### 1. Historial de conversación — ❌ Pendiente
**Impacto:** Transforma completamente la experiencia — el usuario puede preguntar *"qué fue ese gasto de ayer?"* o *"cambia el monto a 500"* de forma natural.

**Implementación:**
- Nuevo SK en DynamoDB: `MSG#<timestamp>` con `role` (user/assistant) y `content`
- Al llamar a Claude, recuperar los últimos 10 mensajes del usuario y pasarlos como `messages[]`
- Ventana deslizante: solo guardar los últimos N mensajes para controlar costos

**Archivos afectados:** `dynamo.py`, `parser.py`, `handler.py`

---

#### 2. Sistema de presupuestos — ❌ Pendiente
**Impacto:** Permite al usuario definir límites de gasto y recibir alertas automáticas.

**Implementación:**
- Nuevo SK: `BUDGET#<categoria>#<año-mes>` (ej. `BUDGET#lujos#2026-06`)
- Nueva tool de Claude: `definir_presupuesto`
- En `register_transaction`: comparar gasto acumulado vs. presupuesto del mes y notificar si supera el 80% o el 100%

**Archivos afectados:** `dynamo.py`, `parser.py`, `responses.py`

---

#### 3. Editar y eliminar transacciones — ✅ Edición implementada / ❌ Eliminación pendiente

**Implementado:** corrección de `monto` y `categoria` mediante `corregir_transaccion` (Claude tool). Soporta hasta las últimas 20 transacciones.

**Pendiente:** eliminación de transacciones.
- Para borrar: marcar el item con `deleted: true` y compensar el balance con `ADD` negativo

**Archivos afectados:** `dynamo.py`, `parser.py`, `handler.py`

---

#### 4. Prompt caching — ✅ Implementado
**Impacto:** Reduce el costo de llamadas a Claude ~90% en tráfico repetido.

**Implementación:**
- Agregar `cache_control: {"type": "ephemeral"}` al bloque `system` en `parser.py`
- La caché del system prompt dura 5 minutos en el API de Anthropic
- Sin cambios en infraestructura

**Archivos afectados:** `parser.py`

```python
# parser.py — cambio puntual en _client.messages.create
system=[{
    "type": "text",
    "text": _SYSTEM_PROMPT.format(today=date.today().isoformat()),
    "cache_control": {"type": "ephemeral"},
}]
```

---

#### 5. Comandos de Telegram (/commands) — ✅ Implementado

**Comandos disponibles:**

| Comando | Acción |
|---|---|
| `/historial` | Últimas 10 transacciones (sin LLM) |
| `/historial N` | Últimas N transacciones, máx 20 |
| `/balance` | Balance total inmediato |
| `/hoy` | Gastos del día por categoría |
| `/semana` | Gastos de esta semana por categoría |
| `/mes` | Gastos del mes en curso por categoría |
| `/ayuda` | Lista de comandos disponibles |

Detección en `_handle_command()` dentro de `finance_processor/handler.py` — los comandos `/` se resuelven directamente contra DynamoDB sin llamar a Claude.

**Archivos afectados:** `handler.py`, `responses.py`

---

### Media prioridad

#### 6. Dashboard web
**Stack:** API Gateway (rutas REST) + S3 (frontend estático) + CloudFront + Chart.js

Los datos ya están bien estructurados en DynamoDB. Requiere:
- Nueva Lambda `api_handler` que exponga endpoints REST autenticados
- Frontend estático con gráficas de gasto por categoría y línea de tiempo
- Cognito o JWT simple para autenticación

---

#### 7. GSI para consultas por categoría
El stub ya está comentado en `dynamodb.tf`. Habilitar el GSI permite:
- Consultas de todas las transacciones de una categoría sin escanear todo el historial del usuario
- Futuros reportes cross-usuario

```hcl
# dynamodb.tf — descomentar el bloque GSI existente
attribute { name = "GSI1PK" type = "S" }
attribute { name = "GSI1SK" type = "S" }
global_secondary_index {
  name            = "categoria-fecha-index"
  hash_key        = "GSI1PK"
  range_key       = "GSI1SK"
  projection_type = "ALL"
}
```

**Patrón de acceso:** `GSI1PK = USER#<id>#CAT#<categoria>`, `GSI1SK = TX#<timestamp>`

---

#### 8. DLQ + CloudWatch alarms
La invocación async de `finance_processor` falla silenciosamente hoy. Con:
- `dead_letter_config` en la Lambda apuntando a un SQS
- Alarma en CloudWatch sobre `Errors` y `DeadLetterErrors`
- Alerta por email via SNS

El sistema se vuelve observable en producción.

---

### Baja prioridad (Fase 3)

| Feature | Descripción |
|---|---|
| Transacciones recurrentes | EventBridge Scheduler + nuevo SK `RECUR#<id>` |
| Exportar CSV / PDF | Lambda bajo demanda que genera un archivo y lo envía por Telegram |
| Multi-moneda | Agregar campo `moneda` en `TX#` y conversión al consultar balance |
| Notificaciones proactivas | EventBridge diario: "No has registrado gastos en 3 días" o "Ya superaste tu presupuesto en lujos" |

---

### Orden recomendado de implementación

```
✅ /commands de Telegram (hecho)
✅ Edición de transacciones (hecho)
✅ Prompt caching (hecho)
⬜ Historial de conversación (2 días)
⬜ Eliminación de transacciones (medio día)
⬜ Sistema de presupuestos (2 días)
⬜ DLQ + alarmas (1 día)
⬜ Dashboard web (1 semana)
```

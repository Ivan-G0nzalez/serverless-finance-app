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
```

## Categorías de Gasto

| Categoría | Descripción |
|---|---|
| `gastos` | Necesidades cotidianas (comida, transporte, salud) |
| `lujos` | Gastos no esenciales (entretenimiento, viajes) |
| `regalos` | Regalos y donaciones |

Para agregar una categoría: actualizar `CATEGORIES` en `dynamo.py` y el system prompt en `parser.py`.

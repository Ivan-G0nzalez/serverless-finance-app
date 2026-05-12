# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Deploy Commands

```bash
# 1. Build the Lambda layer (run once or when requirements change)
pip install -r layers/requirements.txt -t layers/python/

# 2. Deploy infrastructure
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

# 3. Register Telegram webhook after deploy
TELEGRAM_BOT_TOKEN=<token> python scripts/set_webhook.py $(terraform output -raw api_gateway_url)
```

`terraform/terraform.tfvars` is gitignored — copy from `.env.example` and fill in credentials.

## Architecture

Two Lambdas communicate asynchronously:

1. **`webhook_handler`** — invoked by API Gateway on every Telegram POST. Parses the update, immediately returns HTTP 200 to Telegram (avoids timeout), then invokes `finance_processor` asynchronously (`InvocationType=Event`).

2. **`finance_processor`** — receives `{chat_id, user_id, text}`. Calls Claude Haiku via `parser.py` to classify the message into a structured action, writes to DynamoDB, then sends the reply back to Telegram directly.

The async invocation pattern is intentional: Telegram requires a response in under 5 seconds, while Claude + DynamoDB can take longer.

## DynamoDB Single-Table Design

Table name: `finanzas`. All items share `PK = USER#<telegram_user_id>`.

| SK pattern | Purpose |
|---|---|
| `PROFILE` | User record, created on first message |
| `TX#<ISO timestamp>` | Individual transaction (gasto or ingreso) |
| `BALANCE#total` | Running totals: `total_ingresos`, `total_gastos` |
| `BALANCE#gastos` | Running total for category *gastos* |
| `BALANCE#lujos` | Running total for category *lujos* |
| `BALANCE#regalos` | Running total for category *regalos* |

Balances are updated atomically with `ADD` expressions at write time — there is no aggregation query at read time. Amounts are stored as `Decimal` (DynamoDB requirement; never use `float` directly with boto3).

## Fixed Expense Categories

The three categories are hardcoded in `dynamo.py:CATEGORIES` and in the Claude system prompt in `parser.py`:
- **gastos** — everyday needs (food, transport, utilities, health)
- **lujos** — non-essential spending (entertainment, travel, luxury items)
- **regalos** — gifts and donations

To add a category: update `CATEGORIES` in `dynamo.py` and the system prompt in `parser.py`.

## Environment Variables

| Variable | Used by | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | both Lambdas | Telegram Bot API token |
| `ANTHROPIC_API_KEY` | `finance_processor` | Claude API key |
| `DYNAMODB_TABLE` | `finance_processor` | DynamoDB table name (`finanzas`) |
| `FINANCE_PROCESSOR_ARN` | `webhook_handler` | ARN for async invocation |

## Lambda Packaging

Terraform zips each Lambda directory automatically via `archive_file` data sources in `lambda.tf`. Dependencies (only `anthropic`) go into a Lambda Layer defined in `layers.tf`. `boto3` is not in `requirements.txt` — it is provided by the Lambda runtime.

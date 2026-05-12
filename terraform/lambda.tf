# --- IAM ---

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = { Project = var.project_name }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dynamo_access" {
  name = "${var.project_name}-dynamo-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
      ]
      Resource = aws_dynamodb_table.finanzas.arn
    }]
  })
}

resource "aws_iam_role_policy" "invoke_processor" {
  name = "${var.project_name}-invoke-processor"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.finance_processor.arn
    }]
  })
}

# --- Empaquetado ---

data "archive_file" "webhook_handler" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/webhook_handler"
  output_path = "${path.module}/../builds/webhook_handler.zip"
}

data "archive_file" "finance_processor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/finance_processor"
  output_path = "${path.module}/../builds/finance_processor.zip"
}

# --- Lambdas ---

resource "aws_lambda_function" "webhook_handler" {
  function_name    = "${var.project_name}-webhook-handler"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = var.lambda_runtime
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.webhook_handler.output_path
  source_code_hash = data.archive_file.webhook_handler.output_base64sha256
  timeout          = 10
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TELEGRAM_BOT_TOKEN    = var.telegram_bot_token
      FINANCE_PROCESSOR_ARN = aws_lambda_function.finance_processor.arn
    }
  }

  tags = { Project = var.project_name }
}

resource "aws_lambda_function" "finance_processor" {
  function_name    = "${var.project_name}-finance-processor"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = var.lambda_runtime
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.finance_processor.output_path
  source_code_hash = data.archive_file.finance_processor.output_base64sha256
  timeout          = 30
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TELEGRAM_BOT_TOKEN = var.telegram_bot_token
      ANTHROPIC_API_KEY  = var.anthropic_api_key
      DYNAMODB_TABLE     = var.dynamodb_table_name
    }
  }

  tags = { Project = var.project_name }
}

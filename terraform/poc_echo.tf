# --- Prueba de concepto: endpoint que recibe un body y lo retorna tal cual ---
# Pensado para probar la automatización de iPhone que reenvía notificaciones
# de pago del banco. Sin autenticación — reemplazar antes de manejar datos reales.

resource "aws_iam_role" "echo_lambda_exec" {
  name = "${var.project_name}-echo-exec"

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

resource "aws_iam_role_policy_attachment" "echo_lambda_basic_logs" {
  role       = aws_iam_role.echo_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "echo_handler" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/echo_handler"
  output_path = "${path.module}/../builds/echo_handler.zip"
}

resource "aws_lambda_function" "echo_handler" {
  function_name    = "${var.project_name}-echo"
  role             = aws_iam_role.echo_lambda_exec.arn
  runtime          = var.lambda_runtime
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.echo_handler.output_path
  source_code_hash = data.archive_file.echo_handler.output_base64sha256
  timeout          = 10

  tags = { Project = var.project_name }
}

resource "aws_api_gateway_resource" "echo" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "echo"
}

resource "aws_api_gateway_method" "post_echo" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.echo.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "echo_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.echo.id
  http_method             = aws_api_gateway_method.post_echo.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.echo_handler.invoke_arn
}

resource "aws_lambda_permission" "api_gw_echo" {
  statement_id  = "AllowAPIGatewayInvokeEcho"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.echo_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

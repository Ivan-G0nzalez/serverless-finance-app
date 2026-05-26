resource "aws_lambda_layer_version" "deps" {
  layer_name          = "${var.project_name}-deps"
  filename            = "${path.module}/../builds/lambda_layer.zip"
  source_code_hash    = filebase64sha256("${path.module}/../builds/lambda_layer.zip")
  compatible_runtimes = [var.lambda_runtime]
  description         = "anthropic + requests para app-finanzas"
}

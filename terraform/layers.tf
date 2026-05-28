resource "aws_lambda_layer_version" "deps" {
  layer_name          = "${var.project_name}-deps"
  s3_bucket           = aws_s3_bucket.artifacts.id
  s3_key              = "lambda_layer.zip"
  source_code_hash    = trimspace(file("${path.module}/../builds/lambda_layer.sha256"))
  compatible_runtimes = [var.lambda_runtime]
  description         = "anthropic + openai para app-finanzas"
}

data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../layers"
  output_path = "${path.module}/../builds/lambda_layer.zip"
}

resource "aws_lambda_layer_version" "deps" {
  layer_name          = "${var.project_name}-deps"
  filename            = data.archive_file.lambda_layer.output_path
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
  compatible_runtimes = [var.lambda_runtime]

  description = "anthropic + requests para app-finanzas"
}

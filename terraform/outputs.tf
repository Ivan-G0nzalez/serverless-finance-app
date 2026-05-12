output "api_gateway_url" {
  description = "URL base del API Gateway — úsala para registrar el webhook en Telegram"
  value       = "${aws_api_gateway_deployment.main.invoke_url}${aws_api_gateway_stage.main.stage_name}/webhook"
}

output "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB"
  value       = aws_dynamodb_table.finanzas.name
}

output "webhook_handler_arn" {
  description = "ARN de la Lambda webhook_handler"
  value       = aws_lambda_function.webhook_handler.arn
}

output "finance_processor_arn" {
  description = "ARN de la Lambda finance_processor"
  value       = aws_lambda_function.finance_processor.arn
}

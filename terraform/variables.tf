variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "app-finanzas"
}

variable "dynamodb_table_name" {
  description = "Name of the main DynamoDB table"
  type        = string
  default     = "finanzas"
}

variable "telegram_bot_token" {
  description = "Telegram Bot token from @BotFather"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for Whisper audio transcription"
  type        = string
  sensitive   = true
}

variable "lambda_runtime" {
  description = "Python runtime version for Lambda functions"
  type        = string
  default     = "python3.12"
}

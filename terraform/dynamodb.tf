resource "aws_dynamodb_table" "finanzas" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # GSI para consultas por categoría (fase 2)
  # attribute { name = "GSI1PK" type = "S" }
  # attribute { name = "GSI1SK" type = "S" }
  # global_secondary_index {
  #   name            = "categoria-fecha-index"
  #   hash_key        = "GSI1PK"
  #   range_key       = "GSI1SK"
  #   projection_type = "ALL"
  # }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Project = var.project_name
  }
}

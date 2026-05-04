terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# ── S3 Bucket ────────────────────────────────────────────────
resource "aws_s3_bucket" "kb" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "kb" {
  bucket                  = aws_s3_bucket.kb.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "kb_files" {
  for_each = fileset("${path.module}/../data", "*.json")
  bucket   = aws_s3_bucket.kb.id
  key      = "kb/${each.value}"
  source   = "${path.module}/../data/${each.value}"
  etag     = filemd5("${path.module}/../data/${each.value}")
}

# ── Lambda ───────────────────────────────────────────────────
resource "aws_lambda_function" "chatbot" {
  function_name    = var.lambda_name
  filename         = "${path.module}/../lambda/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/handler.zip")
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512
  role             = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      CACHE_BUST = "1"
    }
  }
}

# ── API Gateway ──────────────────────────────────────────────
resource "aws_apigatewayv2_api" "chatbot" {
  name          = "${var.lambda_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_integration" "chatbot" {
  api_id                 = aws_apigatewayv2_api.chatbot.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.chatbot.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "ask" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "POST /ask"
  target    = "integrations/${aws_apigatewayv2_integration.chatbot.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.chatbot.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.chatbot.execution_arn}/*/*"
}

# ── EventBridge Warm-up ──────────────────────────────────────
resource "aws_cloudwatch_event_rule" "warmup" {
  name                = "${var.lambda_name}-warmup"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "warmup" {
  rule = aws_cloudwatch_event_rule.warmup.name
  arn  = aws_lambda_function.chatbot.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.warmup.arn
}

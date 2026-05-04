output "api_url" {
  description = "Paste this URL into wix_embed.html as API_URL"
  value       = "${aws_apigatewayv2_api.chatbot.api_endpoint}/ask"
}

output "lambda_name" {
  value = aws_lambda_function.chatbot.function_name
}

output "s3_bucket" {
  value = aws_s3_bucket.kb.bucket
}

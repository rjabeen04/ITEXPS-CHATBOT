# ITEXPS Chatbot — Terraform Deployment

Deploys the full chatbot stack into a client's AWS account:
- S3 bucket with KB JSON files
- Lambda function (Nova Micro via Bedrock)
- API Gateway HTTP API (`POST /ask`)
- EventBridge warm-up rule (every 5 min)

## Prerequisites

1. [Terraform](https://developer.hashicorp.com/terraform/install) installed
2. Client's AWS credentials configured:
   ```bash
   aws configure --profile client
   export AWS_PROFILE=client
   ```
3. Bedrock Nova Micro model access enabled in client's account:
   - AWS Console → Amazon Bedrock → Model access → Enable **Nova Micro**
4. Build the Lambda zip:
   ```bash
   cd ../lambda && zip handler.zip handler.py
   ```

## Deploy

```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

## After Deploy

Copy the `api_url` from the Terraform output and update `wix_embed.html`:

```js
const API_URL = "<paste api_url here>";
```

Then paste the contents of `wix_embed.html` into the Wix editor:
**Add → Embed → HTML iframe**

## Tear Down

```bash
terraform destroy
```

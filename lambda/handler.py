import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

BUCKET = "itexps-chatbot-kb"
KEY = "kb.json"

CLAUDE_INFERENCE_PROFILE_ARN = (
    "arn:aws:bedrock:us-east-1:378494867598:"
    "inference-profile/us.anthropic.claude-3-haiku-20240307-v1:0"
)

# Load KB outside handler for speed
kb = json.loads(
    s3.get_object(Bucket=BUCKET, Key=KEY)["Body"].read()
)

def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))

def embed(text):
    res = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(res["body"].read())["embedding"]

def generate_answer(prompt):
    res = bedrock.invoke_model(
        modelId=CLAUDE_INFERENCE_PROFILE_ARN,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        }),
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(res["body"].read())
    if "content" in payload and len(payload["content"]) > 0:
        return payload["content"][0]["text"]
    return "I don't know based on the website."

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        question = body.get("question", "").strip()

        if not question:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Missing question"})
            }

        q_vec = embed(question)
        top_chunks = sorted(kb, key=lambda x: cosine(q_vec, x["vector"]), reverse=True)[:3]
        context_text = "\n".join([c["text"] for c in top_chunks])

        prompt = f"""Answer ONLY using this content:

{context_text}

Question: {question}

If the answer is not found in the content above, say: "I don't know based on the website."
"""
        answer = generate_answer(prompt)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({"answer": answer})
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "AWS service error", "details": str(e)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }

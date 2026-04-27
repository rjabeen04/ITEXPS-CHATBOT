import json
import boto3
from botocore.exceptions import ClientError

# ============================================================
# 1. AWS CLIENTS
# ============================================================
s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# ============================================================
# 2. S3 CONFIGURATION
# ============================================================
BUCKET = "itexps-chatbot-kb"
PREFIX = "kb/"   # folder containing your JSON files

# ============================================================
# 3. CLAUDE MODEL (NO TITAN EMBEDDINGS)
# ============================================================
CLAUDE_INFERENCE_PROFILE_ARN = (
    "arn:aws:bedrock:us-east-1:378494867598:"
    "inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
)

# ============================================================
# 4. CORS HEADERS
# ============================================================
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }

# ============================================================
# 5. LOAD ALL JSON FILES FROM S3 (KB)
# ============================================================
KB_CACHE = None

def list_kb_files():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    objects = resp.get("Contents", [])
    return [obj["Key"] for obj in objects if obj["Key"].endswith(".json")]

def load_json_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    raw = obj["Body"].read().decode("utf-8")
    return json.loads(raw)

def load_knowledge_base():
    kb_entries = []
    for key in list_kb_files():
        data = load_json_from_s3(key)
        kb_entries.append({
            "key": key,
            "title": data.get("title", ""),
            "content": data.get("content", "")
        })
    return kb_entries

# ============================================================
# 6. IMPROVED KEYWORD MATCHING (NO EMBEDDINGS)
# ============================================================
def find_best_match(question, kb):
    q = question.lower()

    best_entry = None
    max_hits = 0

    for entry in kb:
        content = entry["content"].lower()
        title = entry["title"].lower()

        # Count how many words from the question appear in title or content
        hits = sum(
            1 for word in q.split()
            if word in content or word in title
        )

        if hits > max_hits:
            max_hits = hits
            best_entry = entry

    # If nothing matched, fall back to "home" or first file
    if best_entry is None:
        for entry in kb:
            if entry["title"].lower() == "home":
                return entry
        return kb[0]

    return best_entry

# ============================================================
# 7. GENERATE ANSWER USING CLAUDE
# ============================================================
def generate_answer(context_text, question):
    prompt = f"""
You are an ITEXPS assistant. Answer ONLY using the content below.

--------------------
CONTEXT:
{context_text}
--------------------

USER QUESTION:
{question}

If the answer is not found in the context, respond exactly with:
"I don't know based on the website."
"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
    }

    res = bedrock.invoke_model(
        modelId=CLAUDE_INFERENCE_PROFILE_ARN,
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json",
    )

    payload = json.loads(res["body"].read())

    if "content" in payload and len(payload["content"]) > 0:
        return payload["content"][0]["text"]

    return "I don't know based on the website."

# ============================================================
# 8. MAIN LAMBDA HANDLER
# ============================================================
def lambda_handler(event, context):
    global KB_CACHE

    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        question = body.get("question", "").strip()

        if not question:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Missing question"})
            }

        # Load KB once per Lambda container
        if KB_CACHE is None:
            KB_CACHE = load_knowledge_base()

        # Retrieve best matching page
        selected_entry = find_best_match(question, KB_CACHE)

        # Generate answer using Claude
        answer = generate_answer(selected_entry["content"], question)

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "matched_page": selected_entry["title"],
                "answer": answer
            })
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({
                "error": "AWS service error",
                "details": str(e)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }

import json
import boto3
import os
from botocore.exceptions import ClientError

# ============================================================
# 1. AWS CLIENTS
# ============================================================
s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# ============================================================
# 2. S3 CONFIGURATION
# ============================================================
BUCKET = os.environ["S3_BUCKET"]
PREFIX = "kb/"   # folder containing your JSON files

# ============================================================
# 3. NOVA MICRO MODEL
# ============================================================

NOVA_MICRO_ARN = os.environ["BEDROCK_MODEL_ARN"]

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
            "content": data.get("content", ""),
            "url": data.get("url", "https://itexps.com")
        })
    return kb_entries

# ============================================================
# 6. KEYWORD PRIORITY MAP + MATCHING
# ============================================================
KEYWORDS_MAP = {
    # Education & Grants
    "grant":     "educationgrantprogram.json",
    "wioa":      "educationgrantprogram.json",
    "mycaa":     "educationgrantprogram.json",
    "army":      "educationgrantprogram.json",
    # Proctoring
    "proctor":   "proctoringservices.json",
    "exam":      "proctoringservices.json",
    "testing":   "proctoringservices.json",
    "certif":    "proctoringservices.json",
    "clep":      "proctoringservices.json",
    "psi":       "proctoringservices.json",
    "work key":  "proctoringservices.json",
    "remote exam": "proctoringservices.json",
    "faa":       "proctoringservices.json",
    "prometric": "proctoringservices.json",
    "ase":       "proctoringservices.json",
    "certiport": "proctoringservices.json",
    "tofel":     "proctoringservices.json",
    "kryterion": "proctoringservices.json",
    "isq":       "proctoringservices.json",
    "gre":       "proctoringservices.json",
    "toeic":     "proctoringservices.json",
    "scantron":  "proctoringservices.json",
    "tsa":       "proctoringservices.json",
    # IT Staffing
    "staff":     "itstaffing.json",
    "hire":      "itstaffing.json",
    "recruit":   "itstaffing.json",
    # FAQ
    "faq":       "faqs.json",
    # Upcoming Training
    "upcoming":  "upcomingtraining.json",
    "schedule":  "upcomingtraining.json",
    "register":  "upcomingtraining.json",
    # Specialized Career Path
    "career":    "specializedcareerpath.json",
    "path":      "specializedcareerpath.json",
    "specialized": "specializedcareerpath.json",
    # Technical & Training
    "train":     "technicalmanagementprograms.json",
    "devops":    "technicalmanagementprograms.json",
    "technical": "technicalmanagementprograms.json",
    "program":   "technicalmanagementprograms.json",
    "service":   "programs.json",
    "services":   "programs.json",
    # General
    "history":   "about_us.json",
    "contact":   "contact.json",
    "phone":     "contact.json",
    "email":     "contact.json",
    "location":  "contact.json",
}

def find_best_match(question, kb):
    q_words = question.lower().translate(str.maketrans('', '', '?!.,\'')).split()

    STOP_WORDS = {"what", "is", "the", "how", "do", "i", "a", "an", "of", "for",
                  "to", "tell", "me", "about", "are", "can", "you", "your", "us",
                  "we", "my", "in", "on", "at", "and", "or", "it", "this", "that"}

    # Priority: keyword map with substring match, longer keys first
    for word in q_words:
        if word in STOP_WORDS:
            continue
        for base_key, target in sorted(KEYWORDS_MAP.items(), key=lambda x: -len(x[0])):
            if base_key in word:
                match = next((e for e in kb if target in e["key"]), None)
                if match:
                    return match

    # Fallback: word hit counter
    best_entry = None
    max_hits = 0
    for entry in kb:
        combined = (entry["content"] + " " + entry["title"]).lower()
        hits = sum(1 for w in q_words if w not in STOP_WORDS and w in combined)
        if hits > max_hits:
            max_hits = hits
            best_entry = entry

    return best_entry or next((e for e in kb if "home" in e["key"]), kb[0])

# ============================================================
# 7. GENERATE ANSWER USING CLAUDE
# ============================================================
def generate_answer(context_text, question, page_title, page_url):
    prompt = f"""
You are an ITEXPS assistant. Answer ONLY using the content below.
Be concise and professional.

STRICT FORMATTING RULE:
At the end of your answer, provide EXACTLY ONE clickable link in this format:
[{page_title}]({page_url})
Do NOT repeat the raw URL in the text.

--------------------
CONTEXT:
{context_text}
--------------------

USER QUESTION:
{question}

If the answer is not found in the context, respond with:
"I don't have that specific info. Please call 847-350-9034 or visit [Contact Us](https://www.itexps.net/contact-us)."
"""

    response = bedrock.converse(
        modelId=NOVA_MICRO_ARN,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0.1, "topP": 0.9}
    )
    return response["output"]["message"]["content"][0]["text"]

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
        answer = generate_answer(selected_entry["content"], question, selected_entry["title"], selected_entry["url"])

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

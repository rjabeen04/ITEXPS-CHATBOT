# ITExps AI Chatbot & Infrastructure

A serverless, RAG-based (Retrieval-Augmented Generation) AI chatbot designed to provide intelligent, context-aware responses. This project leverages AWS serverless architecture and is fully provisioned using Terraform.

## 🚀 Architecture Overview
The system uses a modular landing zone architecture to deploy a secure and scalable AI environment.

*   **AI/ML:** AWS Bedrock for LLM orchestration and AWS Rekognition for biometric security.
*   **Backend:** AWS Lambda (Python) handles the core logic and Converse API calls.
*   **Infrastructure:** Managed via **Terraform** (Infrastructure as Code) for repeatable deployments.
*   **Security:** Scoped IAM roles following the principle of least privilege.
*   **Storage:** Amazon S3 for data ingestion and project archives.

## 📂 Project Structure
```text
.
├── terraform/          # IaC modules (IAM, Lambda, S3, Provider setup)
├── lambda/             # Python-based Lambda handlers (handler.py)
├── frontend/           # Integration files for Wix/Web platforms
├── data_ingestion/     # Scripts for processing RAG data
└── archive/            # Deployment packages and historical artifacts

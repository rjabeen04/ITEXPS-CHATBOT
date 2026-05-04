# ITExps AI Chatbot & Infrastructure
🏗️ System Architecture

A serverless RAG-based AI chatbot built on AWS that enables context-aware responses using a modular, production-style cloud architecture. The system is fully provisioned using Terraform and integrates AI services with secure backend design principles.

🚀 Architecture Overview

This project follows a modular landing zone approach to design a scalable and secure AI system on AWS.

AI/ML: AWS Bedrock (Claude) for LLM orchestration and AWS Rekognition for biometric verification
Backend: AWS Lambda (Python) handling RAG logic and API execution
Infrastructure: Terraform used for full Infrastructure-as-Code automation
Security: IAM roles designed with least-privilege access control
Storage: Amazon S3 for ingestion data and artifact management
🔑 Key Features
Fully serverless cloud-native architecture
RAG-based chatbot powered by AWS Bedrock
End-to-end Infrastructure as Code using Terraform
Secure biometric authentication using AWS Rekognition
Modular and reusable cloud components
🧠 Architecture Decisions

Why AWS Bedrock instead of OpenAI?
→ Native AWS integration, easier IAM control, and enterprise-grade security alignment

Why AWS Lambda instead of EC2?
→ Event-driven execution, auto-scaling, and zero server management

Why Terraform instead of CloudFormation?
→ Better modularity, multi-cloud capability, and reusable infrastructure patterns

📂 Project Structure
.
├── terraform/          # Infrastructure modules (IAM, Lambda, S3, provider config)
├── lambda/             # Python Lambda functions (core RAG logic)
├── frontend/           # UI integration (web/Wix)
├── data_ingestion/     # Data processing for RAG pipeline
└── archive/            # Deployment artifacts and backups

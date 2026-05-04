# 📘 README – ITExps Chatbot Widget

## 📌 Overview
The **ITExps Chatbot Widget** is a lightweight, embeddable web‑based chat interface that connects to an AWS API Gateway endpoint.  
It allows users to interact with an AI assistant directly from any webpage using a clean, modern UI.

This widget is built using:

- **HTML** for structure  
- **CSS** for styling and animations  
- **JavaScript (Fetch API)** for sending user messages to the backend  
- **AWS API Gateway + Lambda** for processing chatbot responses  

---

## 🚀 Features
- Floating “Chat with ITExps” button  
- Expandable/collapsible chat window  
- Modern UI with message bubbles  
- Auto‑scrolling message container  
- Supports clickable links in bot responses  
- Sends user messages to a backend API using `POST`  
- Displays bot replies dynamically  
- Fully responsive and easy to embed  

---

## 🔧 How It Works

### **1. User types a message**
Captured from:
```js
const text = queryInput.value.trim();

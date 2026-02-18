from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

webhook_url = os.getenv("FEISHU_WEBHOOK")
if not webhook_url:
    print("Error: FEISHU_WEBHOOK is not set in .env")
    exit(1)

print(f"Webhook URL configured: {webhook_url[:10]}...")

payload = {
    "msg_type": "text",
    "content": {
        "text": "🔍 Test Message from OptoAgent Debug Script"
    }
}

try:
    print(f"Sending test message to {webhook_url}...")
    response = requests.post(webhook_url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    response.raise_for_status()
    print("✅ Success! Message sent.")
except Exception as e:
    print(f"❌ Failed to send: {e}")

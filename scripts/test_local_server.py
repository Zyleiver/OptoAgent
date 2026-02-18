import requests
import json
import time

url = "http://localhost:5000/feishu_webhook"
data = {
    "header": {
        "event_type": "im.message.receive_v1"
    },
    "event": {
        "message": {
            "content": "{\"text\":\"search spectrometer\"}",
            "message_type": "text"
        }
    }
}

try:
    print(f"Sending mock request to {url}...")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

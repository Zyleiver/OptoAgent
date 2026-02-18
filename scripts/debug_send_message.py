from dotenv import load_dotenv
import os
import sys
sys.path.append("src")
from src.modules.notifier import FeishuNotifier

load_dotenv()

chat_id = "oc_961450eb555e044509a9224cfbd4b091"
notifier = FeishuNotifier()

print(f"Attempting to send message to Chat ID: {chat_id}")

try:
    notifier.send_text("🔍 Debug Test Message", receive_id=chat_id)
except Exception as e:
    print(f"Exception: {e}")

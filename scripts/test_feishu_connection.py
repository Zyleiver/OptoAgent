from dotenv import load_dotenv
import os
import sys
sys.path.append("src")

from src.modules.notifier import FeishuNotifier

load_dotenv()

print("Using credentials:")
print(f"APP_ID: {os.getenv('APP_ID')}")
print(f"APP_SECRET: {'*' * 10 if os.getenv('APP_SECRET') else 'MISSING'}")

notifier = FeishuNotifier()
token = notifier.get_tenant_access_token()

if token:
    print(f"✅ Success! Tenant Access Token retrieved: {token[:10]}...")
else:
    print("❌ Failed to retrieve Tenant Access Token. Check APP_ID and APP_SECRET.")

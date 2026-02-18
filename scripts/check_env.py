from dotenv import load_dotenv
import os

load_dotenv()

keys = ["APP_ID", "APP_SECRET", "FEISHU_WEBHOOK"]
print("Environment Key Check:")
for key in keys:
    val = os.getenv(key)
    status = "PRESENT" if val and len(val) > 0 else "MISSING"
    print(f"{key}: {status}")

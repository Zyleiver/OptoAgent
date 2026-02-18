from flask import Flask, request, jsonify
import sys
import subprocess
import threading

app = Flask(__name__)

def run_search(query):
    """
    Run active_search in a background thread to avoid blocking the webhook.
    """
    print(f"Triggering search for: {query}")
    subprocess.run([sys.executable, "src/main.py", "run_cycle", "--query", query, "--limit", "3"])

@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    """
    Handle Feishu Event Callback.
    1. Authorization Challenge (First time setup)
    2. Message Events
    """
    data = request.json
    
    # 1. Handle Challenge (URL Verification)
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    
    # 2. Handle Message Event
    # Feishu 2.0 event format check
    if "header" in data and data["header"].get("event_type") == "im.message.receive_v1":
        event = data.get("event", {})
        message = event.get("message", {})
        content = message.get("content", "")
        
        # Helper to parse text content (it comes as JSON string inside string)
        import json
        try:
            text_content = json.loads(content).get("text", "")
        except:
            text_content = content

        print(f"Received message: {text_content}")
        
        # Simple Logic: If message starts with "search" or "research", trigger agent
        if text_content.strip().lower().startswith("search") or text_content.strip().lower().startswith("research"):
            query = text_content.strip().split(" ", 1)[1] if " " in text_content else "perovskite"
            
            # Run in separate thread
            thread = threading.Thread(target=run_search, args=(query,))
            thread.start()
            
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("Starting Feishu Interaction Server on port 5000...")
    app.run(host="0.0.0.0", port=5000)

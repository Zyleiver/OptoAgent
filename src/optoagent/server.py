"""
Flask server for Feishu webhook interactions.

Receives messages from Feishu, dispatches search tasks in background threads.
"""

import json
import re
import subprocess
import sys
import threading

from flask import Flask, jsonify, request

from optoagent.config import DEFAULT_QUERY
from optoagent.logger import get_logger
from optoagent.modules.notifier import FeishuNotifier

logger = get_logger(__name__)

app = Flask(__name__)
notifier = FeishuNotifier()


def _run_search(query: str, chat_id: str | None = None) -> None:
    """Run run_cycle in a background thread to avoid blocking the webhook."""
    logger.info("Triggering search for: %s (Chat ID: %s)", query, chat_id)

    cmd = [sys.executable, "-m", "optoagent.cli", "run_cycle", "--query", query, "--limit", "5"]
    if chat_id:
        cmd.extend(["--chat_id", chat_id])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        logger.info("Subprocess Output:\n%s", result.stdout)
        if result.stderr:
            logger.warning("Subprocess Error:\n%s", result.stderr)
    except Exception as e:
        logger.error("Subprocess failed: %s", e)


@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    """Handle Feishu Event Callback."""
    data = request.json
    logger.info("Received webhook request: %s", json.dumps(data, ensure_ascii=False)[:500])

    # 1. Handle Challenge verification
    if "challenge" in data:
        logger.info("Challenge request received, responding...")
        return jsonify({"challenge": data["challenge"]})

    # 2. Handle Message Event
    if "header" in data and data["header"].get("event_type") == "im.message.receive_v1":
        event = data.get("event", {})
        message = event.get("message", {})
        content = message.get("content", "")
        msg_type = message.get("message_type", "")
        chat_id = message.get("chat_id")

        logger.info("Message type: %s | Chat ID: %s | Raw content: %s", msg_type, chat_id, content)

        try:
            text_content = json.loads(content).get("text", "")
        except (json.JSONDecodeError, AttributeError):
            text_content = content

        # Strip @mention markers
        text_content = re.sub(r"@\S+\s*", "", text_content).strip()
        logger.info("Parsed message: '%s'", text_content)

        # Dispatch: messages starting with "search" or "research"
        if text_content.lower().startswith(("search", "research")):
            query = text_content.split(" ", 1)[1] if " " in text_content else DEFAULT_QUERY
            logger.info("Search query extracted: '%s'", query)

            notifier.send_text(
                f"🔍收到指令：'{query}'\n正在搜索并生成Idea，请稍候...",
                receive_id=chat_id,
            )

            thread = threading.Thread(target=_run_search, args=(query, chat_id))
            thread.start()
        else:
            logger.info("Message did not match search/research pattern, ignoring.")
    else:
        logger.info("Not a message event, ignoring.")

    return jsonify({"status": "ok"})


def main() -> None:
    logger.info("Starting Feishu Interaction Server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()

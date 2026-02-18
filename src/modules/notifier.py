import requests
import json
from typing import Optional
from models import Paper, Idea

class FeishuNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def send_text(self, text: str):
        if not self.webhook_url:
            print(f"[Feishu Mock] {text}")
            return

        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print("Message sent to Feishu.")
        except Exception as e:
            print(f"Failed to send to Feishu: {e}")

    def notify_new_paper(self, paper: Paper):
        title = f"📄 New Paper Found: {paper.title}"
        content = f"Authors: {', '.join(paper.authors)}\nLink: {paper.url}\n\nSummary: {paper.summary}"
        self.send_text(f"{title}\n\n{content}")

    def notify_new_idea(self, idea: Idea):
        title = f"💡 New Idea Generated: {idea.title}"
        content = f"{idea.description}\n\nReasoning:\n{idea.reasoning}"
        self.send_text(f"{title}\n\n{content}")

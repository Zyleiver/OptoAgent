"""
Feishu (Lark) notification module.

Supports two channels:
  1. App API (preferred) — sends to specific chat_id / user_id
  2. Webhook (fallback)  — sends to a group chat bot
"""

import json
import time
from typing import Optional

import requests

from optoagent.config import APP_ID, APP_SECRET, FEISHU_WEBHOOK
from optoagent.logger import get_logger
from optoagent.models import Idea, Paper

logger = get_logger(__name__)


class FeishuNotifier:
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ):
        self.app_id = app_id or APP_ID
        self.app_secret = app_secret or APP_SECRET
        self.webhook_url = webhook_url or FEISHU_WEBHOOK

        self.token: Optional[str] = None
        self.token_expire_time: float = 0

    # ---- Token management ----

    def get_tenant_access_token(self) -> Optional[str]:
        """Fetch tenant_access_token from Feishu. Refreshes if expired."""
        if self.token and time.time() < self.token_expire_time:
            return self.token

        if not self.app_id or not self.app_secret:
            logger.warning("APP_ID or APP_SECRET not configured. Cannot get token.")
            return None

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                self.token = data.get("tenant_access_token")
                self.token_expire_time = time.time() + data.get("expire", 7200) - 60
                return self.token
            else:
                logger.error("Failed to get tenant_access_token: %s", data.get("msg"))
                return None
        except Exception as e:
            logger.error("Error fetching token: %s", e)
            return None

    # ---- Sending ----

    def send_text(self, text: str, receive_id: Optional[str] = None) -> None:
        """
        Send text message via App API (preferred) or Webhook (fallback).

        :param receive_id: chat_id, open_id, or user_id.
        """
        # Strategy 1: Use App API if receive_id and creds are available
        if receive_id and self.app_id and self.app_secret:
            token = self.get_tenant_access_token()
            if token:
                url = "https://open.feishu.cn/open-apis/im/v1/messages"
                params = {"receive_id_type": "chat_id"}
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                }
                payload = {
                    "receive_id": receive_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text}),
                }

                try:
                    response = requests.post(url, params=params, headers=headers, json=payload)
                    if response.status_code != 200:
                        logger.error("API Send Failed: %s", response.text)
                    else:
                        logger.info("Message sent via App API.")
                    return
                except Exception as e:
                    logger.error("Failed to send via API: %s", e)

        # Strategy 2: Fallback to Webhook
        if self.webhook_url:
            payload = {"msg_type": "text", "content": {"text": text}}
            try:
                resp = requests.post(self.webhook_url, json=payload, timeout=10)
                resp_data = resp.json()
                if resp.status_code == 200 and resp_data.get("code") == 0:
                    logger.info("Message sent via Webhook (fallback).")
                else:
                    logger.error("Webhook returned error: status=%s body=%s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("Webhook send failed: %s", e)
        else:
            logger.info("[Feishu Mock] (No credentials/webhook) %s", text)

    # ---- Convenience methods ----

    def notify_new_paper(self, paper: Paper, receive_id: Optional[str] = None) -> None:
        title = f"📄 New Paper Found: {paper.title}"
        content = f"Authors: {', '.join(paper.authors)}\nLink: {paper.url}\n\nSummary: {paper.summary}"
        self.send_text(f"{title}\n\n{content}", receive_id)

    def notify_new_idea(self, idea: Idea, receive_id: Optional[str] = None) -> None:
        title = f"💡 New Idea Generated: {idea.title}"
        content = f"{idea.description}\n\nReasoning:\n{idea.reasoning}"
        self.send_text(f"{title}\n\n{content}", receive_id)

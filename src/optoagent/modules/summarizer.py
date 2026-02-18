"""
LLM-based paper summarization module.
"""

from typing import Optional

from optoagent.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from optoagent.logger import get_logger
from optoagent.models import Paper

logger = get_logger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class PaperSummarizer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        base_url = base_url or OPENAI_BASE_URL

        self.client = (
            OpenAI(api_key=self.api_key, base_url=base_url)
            if self.api_key and OpenAI
            else None
        )

    def summarize(self, paper: Paper) -> str:
        """Summarize a paper using an LLM."""
        if not self.client:
            return self._summarize_simulated(paper)

        try:
            prompt = f"""Please summarize the following paper for a researcher:

Title: {paper.title}
Authors: {', '.join(paper.authors)}
Abstract: {paper.abstract if paper.abstract else 'Not available'}

Instructions:
1. If the abstract is available, summarize the key innovations and results.
2. If the abstract is MISSING, do NOT apologize. Instead, infer the likely research topic and significance based ONLY on the title. State clearly that this is an inference based on the title.
3. Keep it concise (under 200 words)."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("LLM Summarization failed: %s", e)
            return self._summarize_simulated(paper)

    def _summarize_simulated(self, paper: Paper) -> str:
        return f"[Simulated Summary] {paper.title} is about {paper.abstract[:50]}..."

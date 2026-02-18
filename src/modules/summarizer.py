from models import Paper
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class PaperSummarizer:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url) if self.api_key and OpenAI else None
        self.model = model

    def summarize(self, paper: Paper) -> str:
        """
        Summarizes a paper using an LLM.
        """
        if not self.client:
            return self._summarize_simulated(paper)

        try:
            prompt = f"Please summarize the following paper for a researcher:\n\nTitle: {paper.title}\nAuthors: {', '.join(paper.authors)}\nAbstract: {paper.abstract}\n\nFocus on the key innovations and results."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Summarization failed: {e}")
            return self._summarize_simulated(paper)

    def _summarize_simulated(self, paper: Paper) -> str:
        return f"[Simulated Summary] {paper.title} is about {paper.abstract[:50]}..."

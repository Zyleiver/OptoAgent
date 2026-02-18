from models import Paper
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class PaperSummarizer:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        self.client = OpenAI(api_key=self.api_key, base_url=base_url) if self.api_key and OpenAI else None



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

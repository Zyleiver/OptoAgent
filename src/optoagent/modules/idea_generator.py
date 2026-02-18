"""
LLM-based research idea generator using Chain-of-Thought reasoning.
"""

from typing import List, Optional

from optoagent.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from optoagent.logger import get_logger
from optoagent.models import Experiment, Idea, Paper

logger = get_logger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class IdeaGenerator:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        base_url = OPENAI_BASE_URL
        self.client = (
            OpenAI(api_key=self.api_key, base_url=base_url)
            if self.api_key and OpenAI
            else None
        )

    def generate_idea(
        self,
        papers: List[Paper],
        experiments: List[Experiment],
        context: str = "",
    ) -> Idea:
        """Generate a research idea using CoT reasoning."""
        logger.info("Generating idea using Chain of Thought...")
        if self.client:
            return self._generate_with_llm(papers, experiments, context)
        return self._generate_simulated(papers, experiments)

    def _generate_with_llm(
        self,
        papers: List[Paper],
        experiments: List[Experiment],
        context: str = "",
    ) -> Idea:
        papers_text = "\n".join(
            [f"- {p.title}: {p.summary or p.abstract[:200]}" for p in papers]
        )
        experiments_text = (
            "\n".join(
                [
                    f"- {e.title}: {e.description} (Status: {e.status}, Results: {e.results})"
                    for e in experiments
                ]
            )
            or "No internal experiments recorded yet."
        )

        context_text = ""
        if context:
            context_text = f"\n## Internal Knowledge Base (Relevant Notes):\n{context}\n"

        prompt = f"""You are a research idea generator for an optoelectronics lab.

Based on the following recent papers, internal experiments, and knowledge base notes, propose ONE novel research idea.

## Recent Papers:
{papers_text}

## Internal Experiments:
{experiments_text}
{context_text}
## Instructions:
Use Chain-of-Thought reasoning:
1. Identify key trends and gaps from the papers.
2. Find connections with internal experiments and knowledge base notes.
3. Propose a specific, actionable experiment.
4. Assess feasibility.

## Output Format (strictly follow):
TITLE: [one-line title]
DESCRIPTION: [2-3 sentence description]
REASONING: [your step-by-step reasoning]
SOURCE_PAPERS: [comma-separated list of paper titles used]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative research assistant specializing in optoelectronics and photovoltaics.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            return self._parse_idea(content, papers)
        except Exception as e:
            logger.error("LLM Idea Generation failed: %s", e)
            return self._generate_simulated(papers, experiments)

    def _parse_idea(self, content: str, papers: List[Paper]) -> Idea:
        """Parse LLM output into an Idea object."""
        lines = content.strip().split("\n")
        title = "AI-Generated Research Idea"
        description = ""
        reasoning = content  # fallback: use full content as reasoning
        source_papers = [p.title for p in papers[:3]]

        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                description = line.replace("DESCRIPTION:", "").strip()
            elif line.startswith("SOURCE_PAPERS:"):
                source_papers = [
                    s.strip() for s in line.replace("SOURCE_PAPERS:", "").split(",")
                ]

        # Extract reasoning block
        if "REASONING:" in content:
            reasoning = content.split("REASONING:")[1].split("SOURCE_PAPERS:")[0].strip()

        return Idea(
            title=title,
            description=description or title,
            reasoning=reasoning,
            source_papers=source_papers,
        )

    def _generate_simulated(
        self, papers: List[Paper], experiments: List[Experiment]
    ) -> Idea:
        reasoning = f"[Simulated] Analyzed {len(papers)} papers and {len(experiments)} experiments."
        return Idea(
            title=f"Hybrid Approach using {papers[0].title if papers else 'New Material'}",
            description="Simulated idea - connect a real LLM to enable AI-powered reasoning.",
            reasoning=reasoning,
            source_papers=[p.title for p in papers[:2]],
        )

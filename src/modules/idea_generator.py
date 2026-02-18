from typing import List
from models import Paper, Experiment, Idea
import random

class IdeaGenerator:
    def __init__(self, model_name: str = "gemini-pro"):
        self.model_name = model_name

    def generate_idea(self, papers: List[Paper], experiments: List[Experiment]) -> Idea:
        """
        Simulates generating a research idea based on papers and internal experiments.
        """
        print("Generating idea using Chain of Thought...")
        
        # Simulated Reasoning Process
        reasoning_steps = [
            f"1. Analyzed {len(papers)} new papers and {len(experiments)} internal experiments.",
            "2. Identified a gap: Current experiments focus on stability, but Paper A suggests a new material for efficiency.",
            "3. Hypothesis: Combining our encapsulation technique (Experiment 1) with the material from Paper A could improve both.",
            "4. Feasibility Check: We have the equipment for encapsulation. Material A is commercially available.",
            "5. Conclusion: Propose a new experiment series."
        ]
        reasoning = "\n".join(reasoning_steps)
        
        # Mock Idea
        idea_title = f"Hybrid Approach using {papers[0].title if papers else 'New Material'} and Internal Techniques"
        description = "Develop a new device structure integrating our proprietary passivation layer with the high-mobility transport layer described in the literature."
        
        source_titles = [p.title for p in papers[:2]]
        
        return Idea(
            title=idea_title,
            description=description,
            reasoning=reasoning,
            source_papers=source_titles
        )

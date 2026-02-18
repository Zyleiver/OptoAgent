import json
import os
from typing import List, Dict, Any
from dataclasses import asdict
from models import Paper, Experiment, Idea

class KnowledgeBase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.papers_file = os.path.join(data_dir, "papers.json")
        self.experiments_file = os.path.join(data_dir, "experiments.json")
        self.ideas_file = os.path.join(data_dir, "ideas.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_data(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save_data(self, filepath: str, data: List[Dict[str, Any]]):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_paper(self, paper: Paper):
        papers = self._load_data(self.papers_file)
        # Simple deduplication by title (case-insensitive)
        if any(p['title'].lower() == paper.title.lower() for p in papers):
            print(f"Paper '{paper.title}' already exists.")
            return
        papers.append(asdict(paper))
        self._save_data(self.papers_file, papers)
        print(f"Added paper: {paper.title}")

    def get_papers(self) -> List[Paper]:
        data = self._load_data(self.papers_file)
        return [Paper(**p) for p in data]

    def add_experiment(self, experiment: Experiment):
        experiments = self._load_data(self.experiments_file)
        experiments.append(asdict(experiment))
        self._save_data(self.experiments_file, experiments)
        print(f"Added experiment: {experiment.title}")

    def get_experiments(self) -> List[Experiment]:
        data = self._load_data(self.experiments_file)
        return [Experiment(**p) for p in data]
    
    def add_idea(self, idea: Idea):
        ideas = self._load_data(self.ideas_file)
        ideas.append(asdict(idea))
        self._save_data(self.ideas_file, ideas)
        print(f"Added idea: {idea.title}")

    def get_ideas(self) -> List[Idea]:
        data = self._load_data(self.ideas_file)
        return [Idea(**p) for p in data]

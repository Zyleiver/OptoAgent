"""
JSON-based storage layer for Papers, Experiments, and Ideas.

Handles CRUD operations and file persistence.
"""

import json
import os
from dataclasses import asdict
from typing import Any, Dict, List

from optoagent.config import DATA_DIR
from optoagent.logger import get_logger
from optoagent.models import Experiment, Idea, Paper

logger = get_logger(__name__)


class Storage:
    """Manages JSON-based persistence for Papers, Experiments, and Ideas."""

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.papers_file = os.path.join(self.data_dir, "papers.json")
        self.experiments_file = os.path.join(self.data_dir, "experiments.json")
        self.ideas_file = os.path.join(self.data_dir, "ideas.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)

    def _load_data(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Failed to parse %s, returning empty list.", filepath)
                return []

    def _save_data(self, filepath: str, data: List[Dict[str, Any]]) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ---- Papers ----

    def add_paper(self, paper: Paper) -> None:
        papers = self._load_data(self.papers_file)
        if any(p["title"].lower() == paper.title.lower() for p in papers):
            logger.info("Paper already exists: %s", paper.title)
            return
        papers.append(asdict(paper))
        self._save_data(self.papers_file, papers)
        logger.info("Added paper: %s", paper.title)

    def get_papers(self) -> List[Paper]:
        return [Paper(**p) for p in self._load_data(self.papers_file)]

    # ---- Experiments ----

    def add_experiment(self, experiment: Experiment) -> None:
        experiments = self._load_data(self.experiments_file)
        experiments.append(asdict(experiment))
        self._save_data(self.experiments_file, experiments)
        logger.info("Added experiment: %s", experiment.title)

    def get_experiments(self) -> List[Experiment]:
        return [Experiment(**p) for p in self._load_data(self.experiments_file)]

    # ---- Ideas ----

    def add_idea(self, idea: Idea) -> None:
        ideas = self._load_data(self.ideas_file)
        ideas.append(asdict(idea))
        self._save_data(self.ideas_file, ideas)
        logger.info("Added idea: %s", idea.title)

    def get_ideas(self) -> List[Idea]:
        return [Idea(**p) for p in self._load_data(self.ideas_file)]

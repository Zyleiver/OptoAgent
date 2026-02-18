"""Data models for OptoAgent."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Paper:
    title: str
    authors: List[str]
    abstract: str
    url: str
    summary: Optional[str] = None
    published_date: Optional[str] = None
    found_date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Experiment:
    title: str
    description: str
    results: str
    status: str  # e.g., "ongoing", "completed", "failed"
    date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Idea:
    title: str
    description: str
    reasoning: str
    source_papers: List[str]  # List of paper URLs or titles
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())

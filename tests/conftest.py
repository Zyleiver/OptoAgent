"""
Test fixtures for OptoAgent.
"""

import os
import tempfile

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for tests."""
    return str(tmp_path / "data")


@pytest.fixture
def sample_paper():
    """Return a sample Paper object."""
    from optoagent.models import Paper

    return Paper(
        title="Test Paper on Quantum Dot Spectroscopy",
        authors=["Alice", "Bob"],
        abstract="We demonstrate a novel approach to quantum dot-based spectrometers...",
        url="https://example.com/paper1",
        published_date="2024-01-15",
    )


@pytest.fixture
def sample_experiment():
    """Return a sample Experiment object."""
    from optoagent.models import Experiment

    return Experiment(
        title="QD Film Deposition",
        description="Spin-coating CdSe quantum dots on Si substrate",
        results="Uniform film with 50nm thickness",
        status="completed",
    )


@pytest.fixture
def sample_idea():
    """Return a sample Idea object."""
    from optoagent.models import Idea

    return Idea(
        title="Hybrid QD-Perovskite Spectrometer",
        description="Combine quantum dots with perovskite for broadband spectral sensing.",
        reasoning="QDs provide tunable absorption, perovskites offer high efficiency.",
        source_papers=["Paper A", "Paper B"],
    )

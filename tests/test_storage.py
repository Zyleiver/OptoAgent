"""
Tests for the Storage module.
"""

import json
import os

from optoagent.modules.storage import Storage


class TestStorage:
    def test_add_and_get_paper(self, tmp_data_dir, sample_paper):
        storage = Storage(data_dir=tmp_data_dir)
        storage.add_paper(sample_paper)
        papers = storage.get_papers()

        assert len(papers) == 1
        assert papers[0].title == sample_paper.title
        assert papers[0].url == sample_paper.url

    def test_paper_deduplication(self, tmp_data_dir, sample_paper):
        storage = Storage(data_dir=tmp_data_dir)
        storage.add_paper(sample_paper)
        storage.add_paper(sample_paper)  # duplicate
        papers = storage.get_papers()

        assert len(papers) == 1

    def test_paper_dedup_case_insensitive(self, tmp_data_dir, sample_paper):
        from optoagent.models import Paper

        storage = Storage(data_dir=tmp_data_dir)
        storage.add_paper(sample_paper)

        upper_paper = Paper(
            title=sample_paper.title.upper(),
            authors=sample_paper.authors,
            abstract=sample_paper.abstract,
            url=sample_paper.url,
        )
        storage.add_paper(upper_paper)
        papers = storage.get_papers()

        assert len(papers) == 1

    def test_add_and_get_experiment(self, tmp_data_dir, sample_experiment):
        storage = Storage(data_dir=tmp_data_dir)
        storage.add_experiment(sample_experiment)
        experiments = storage.get_experiments()

        assert len(experiments) == 1
        assert experiments[0].title == sample_experiment.title

    def test_add_and_get_idea(self, tmp_data_dir, sample_idea):
        storage = Storage(data_dir=tmp_data_dir)
        storage.add_idea(sample_idea)
        ideas = storage.get_ideas()

        assert len(ideas) == 1
        assert ideas[0].title == sample_idea.title

    def test_empty_storage(self, tmp_data_dir):
        storage = Storage(data_dir=tmp_data_dir)

        assert storage.get_papers() == []
        assert storage.get_experiments() == []
        assert storage.get_ideas() == []

    def test_corrupted_json(self, tmp_data_dir):
        storage = Storage(data_dir=tmp_data_dir)
        # Write invalid JSON
        os.makedirs(tmp_data_dir, exist_ok=True)
        with open(storage.papers_file, "w") as f:
            f.write("{invalid json")

        assert storage.get_papers() == []

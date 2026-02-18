"""
Tests for PaperSearcher module (simulated mode only).
"""

from optoagent.modules.searcher import PaperSearcher


class TestPaperSearcher:
    def test_simulated_search_returns_papers(self):
        searcher = PaperSearcher(exa_api_key=None)
        papers = searcher.search_active("test query", limit=3)

        assert len(papers) == 3
        assert all(p.title for p in papers)

    def test_simulated_search_contains_query(self):
        searcher = PaperSearcher(exa_api_key=None)
        papers = searcher.search_active("quantum dots", limit=1)

        assert "quantum dots" in papers[0].title

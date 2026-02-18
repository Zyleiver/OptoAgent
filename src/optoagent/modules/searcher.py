"""
Paper search module using Exa.ai and RSS feeds.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import feedparser
import requests

from optoagent.config import ACADEMIC_DOMAINS, RESEARCH_GROUPS, RSS_FEEDS, SEARCH_DAYS_BACK
from optoagent.logger import get_logger
from optoagent.models import Paper
from optoagent.modules.metadata import MetadataEnricher

logger = get_logger(__name__)


class PaperSearcher:
    def __init__(self, exa_api_key: Optional[str] = None):
        self.exa_api_key = exa_api_key
        self._enricher = MetadataEnricher()

    def search_active(self, query: str, limit: int = 5, academic_only: bool = True) -> List[Paper]:
        """Active search using Exa.ai (if key provided) or simulation."""
        if self.exa_api_key:
            return self._search_exa(query, limit, academic_only)
        return self._search_simulated(query, limit)

    def monitor_sources(self) -> List[Paper]:
        """Monitor RSS feeds and Research Groups defined in config.yaml."""
        papers: List[Paper] = []

        # 1. Check RSS Feeds
        if RSS_FEEDS:
            logger.info("Checking %d Journal RSS feeds...", len(RSS_FEEDS))
            papers.extend(self._check_rss_feeds(RSS_FEEDS))

        # 2. Check Research Groups (via Exa)
        if self.exa_api_key and RESEARCH_GROUPS:
            logger.info("Checking %d Research Groups via Exa...", len(RESEARCH_GROUPS))
            for group in RESEARCH_GROUPS:
                group_name = group.get("name", "Unknown")
                query = group.get("query", "")
                logger.info("  Tracking Group: %s", group_name)
                group_papers = self._search_exa(query, limit=3)
                for p in group_papers:
                    p.title = f"[{group_name}] {p.title}"
                papers.extend(group_papers)

        return papers

    # ---- Internal methods ----

    def _check_rss_feeds(self, rss_feeds: List[str]) -> List[Paper]:
        new_papers: List[Paper] = []
        for url in rss_feeds:
            try:
                feed = feedparser.parse(url)
                logger.info("  Parsed RSS %s: %d entries found.", url, len(feed.entries))
                for entry in feed.entries[:3]:
                    p = Paper(
                        title=entry.title,
                        authors=[a.name for a in entry.get("authors", [])] or ["Unknown"],
                        abstract=entry.get("summary", "No abstract available.")[:500],
                        url=entry.link,
                        published_date=entry.get("published", ""),
                    )
                    new_papers.append(p)
            except Exception as e:
                logger.error("Failed to parse RSS %s: %s", url, e)
        return new_papers

    def _search_simulated(self, query: str, limit: int) -> List[Paper]:
        logger.info("[Simulated] Searching for: %s", query)
        return [
            Paper(
                title=f"Simulated Result for {query}",
                authors=["AI Researcher"],
                abstract="This is a placeholder result because no EXA_API_KEY was provided.",
                url="http://example.com/simulated",
                published_date="2024-01-01",
            )
        ] * limit

    def _search_exa(self, query: str, limit: int, academic_only: bool = True) -> List[Paper]:
        logger.info("[Exa] Searching for: %s (Academic Only: %s)", query, academic_only)
        url = "https://api.exa.ai/search"
        headers = {
            "x-api-key": self.exa_api_key,
            "Content-Type": "application/json",
        }

        # Only return papers published within the configured window
        start_date = (datetime.now() - timedelta(days=SEARCH_DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        payload: dict = {
            "query": query,
            "numResults": limit,
            "useAutoprompt": True,
            "startPublishedDate": start_date,
            "contents": {
                "text": True,
                "highlights": {
                    "numSentences": 5,
                    "query": query,
                },
                "summary": True,
            },
        }

        if academic_only:
            payload["includeDomains"] = ACADEMIC_DOMAINS

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            papers = []
            for result in data.get("results", []):
                # Build clean abstract from highlights or summary
                abstract = self._extract_abstract(result)

                # Extract authors
                author_str = result.get("author", "") or ""
                authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []

                p = Paper(
                    title=result.get("title", "No Title"),
                    authors=authors,
                    abstract=abstract,
                    url=result.get("url"),
                    published_date=result.get("publishedDate"),
                )
                papers.append(p)

            # Enrich metadata via Semantic Scholar / CrossRef
            if papers:
                logger.info("[Exa] Enriching metadata for %d papers...", len(papers))
                papers = self._enrich_papers(papers)

            return papers
        except Exception as e:
            logger.error("[Exa] Search failed: %s", e)
            return []

    @staticmethod
    def _extract_abstract(result: dict) -> str:
        """Extract the best abstract from Exa result, preferring summary > highlights > text."""
        # 1. Prefer summary (AI-generated, clean)
        summary = result.get("summary")
        if summary and len(summary.strip()) > 50:
            return summary.strip()

        # 2. Highlights: clean, relevant sentences
        highlights = result.get("highlights")
        if highlights and isinstance(highlights, list):
            # highlights is a list of dicts with "text" or just strings
            sentences = []
            for h in highlights:
                if isinstance(h, dict):
                    sentences.append(h.get("text", ""))
                elif isinstance(h, str):
                    sentences.append(h)
            combined = " ".join(s.strip() for s in sentences if s.strip())
            if len(combined) > 50:
                return combined

        # 3. Fallback: raw text (truncated, stripped of obvious junk)
        text = result.get("text", "")
        if text:
            # Skip the first few lines which often contain nav/cookie junk
            lines = text.split("\n")
            clean_lines = [ln.strip() for ln in lines if len(ln.strip()) > 30 and "cookie" not in ln.lower() and "javascript" not in ln.lower()]
            return " ".join(clean_lines[:10])[:800]

        return "No abstract available."

    def _enrich_papers(self, papers: List[Paper]) -> List[Paper]:
        """Enrich papers with accurate metadata from Semantic Scholar / CrossRef."""
        for p in papers:
            enrichment = self._enricher.enrich_paper(
                title=p.title,
                url=p.url,
                current_authors=p.authors,
                current_abstract=p.abstract,
            )
            if enrichment.get("enriched"):
                source = enrichment["source"]
                # Update authors if enrichment found them
                if enrichment["authors"]:
                    p.authors = enrichment["authors"]
                    logger.info("  ✓ Authors enriched [%s]: %s", source, ", ".join(p.authors[:3]))
                # Update abstract only if Semantic Scholar/CrossRef provides one
                # (keep Exa summary as fallback since it's already clean)
                if enrichment["abstract"] and len(enrichment["abstract"]) > 50:
                    p.abstract = enrichment["abstract"]
                    logger.info("  ✓ Abstract enriched [%s]: %s...", source, p.abstract[:60])
            else:
                logger.debug("  ○ No enrichment for: %s", p.title[:60])
        return papers



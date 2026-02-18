"""
Paper metadata enrichment using Semantic Scholar and CrossRef APIs.

Enriches papers found by Exa with accurate authors and abstracts
by looking up metadata via DOI or title search.
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

import requests

from optoagent.logger import get_logger

logger = get_logger(__name__)

# Rate limiting: Semantic Scholar allows 100 req/5min without key
_SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
_CROSSREF_BASE = "https://api.crossref.org/works"

# Polite delay between API calls (seconds)
_API_DELAY = 0.5


class MetadataEnricher:
    """Enriches paper metadata using Semantic Scholar and CrossRef APIs."""

    def __init__(self, semantic_scholar_api_key: Optional[str] = None):
        self.s2_api_key = semantic_scholar_api_key
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "OptoAgent/1.0 (mailto:optoagent@example.com)",
        })
        if self.s2_api_key:
            self._session.headers["x-api-key"] = self.s2_api_key

    def enrich_paper(self, title: str, url: str, current_authors: List[str],
                     current_abstract: str) -> Dict:
        """
        Enrich a single paper's metadata.

        Returns dict with keys: authors, abstract, enriched (bool), source (str).
        """
        # Step 1: Try to extract DOI from URL
        doi = self._extract_doi(url)

        # Step 2: Try Semantic Scholar by DOI
        if doi:
            result = self._lookup_semantic_scholar_doi(doi)
            if result:
                return result

        # Step 3: Try CrossRef by DOI
        if doi:
            result = self._lookup_crossref_doi(doi)
            if result:
                return result

        # Step 4: Try Semantic Scholar by title search
        result = self._search_semantic_scholar_title(title)
        if result:
            return result

        # Step 5: Fallback — return original data
        logger.info("  Could not enrich metadata for: %s", title[:60])
        return {
            "authors": current_authors,
            "abstract": current_abstract,
            "enriched": False,
            "source": "exa_original",
        }

    # ---- DOI Extraction ----

    @staticmethod
    def _extract_doi(url: str) -> Optional[str]:
        """Extract DOI from common academic publisher URLs."""
        if not url:
            return None

        url = unquote(url)

        # Pattern 1: /doi/10.xxxx/... (science.org, wiley, etc.)
        m = re.search(r'/doi/?(10\.\d{4,}/[^\s?#]+)', url)
        if m:
            return m.group(1).rstrip('/')

        # Pattern 2: nature.com/articles/s41xxx-xxx-xxxxx-x
        m = re.search(r'nature\.com/articles/(s\d+[-\w]+)', url)
        if m:
            article_id = m.group(1)
            # Nature DOIs follow pattern 10.1038/{article_id}
            return f"10.1038/{article_id}"

        # Pattern 3: pubs.acs.org/doi/10.xxxx/...
        m = re.search(r'(10\.\d{4,}/[^\s?#]+)', url)
        if m:
            return m.group(1).rstrip('/')

        return None

    # ---- Semantic Scholar ----

    def _lookup_semantic_scholar_doi(self, doi: str) -> Optional[Dict]:
        """Look up paper by DOI on Semantic Scholar."""
        fields = "title,authors,abstract,year,externalIds"
        api_url = f"{_SEMANTIC_SCHOLAR_BASE}/paper/DOI:{doi}?fields={fields}"

        try:
            time.sleep(_API_DELAY)
            resp = self._session.get(api_url, timeout=10)
            if resp.status_code == 404:
                logger.debug("  S2: DOI not found: %s", doi)
                return None
            if resp.status_code == 429:
                logger.warning("  S2: Rate limited, skipping DOI lookup")
                return None
            resp.raise_for_status()
            data = resp.json()
            return self._parse_s2_result(data, "semantic_scholar_doi")
        except Exception as e:
            logger.debug("  S2 DOI lookup failed: %s", e)
            return None

    def _search_semantic_scholar_title(self, title: str) -> Optional[Dict]:
        """Search Semantic Scholar by title."""
        # Clean title: remove [Group Name] prefix
        clean_title = re.sub(r'^\[.*?\]\s*', '', title).strip()
        if not clean_title or len(clean_title) < 10:
            return None

        fields = "title,authors,abstract,year,externalIds"
        api_url = f"{_SEMANTIC_SCHOLAR_BASE}/paper/search"
        params = {
            "query": clean_title[:200],
            "limit": 3,
            "fields": fields,
        }

        try:
            time.sleep(_API_DELAY)
            resp = self._session.get(api_url, params=params, timeout=10)
            if resp.status_code == 429:
                logger.warning("  S2: Rate limited, skipping title search")
                return None
            resp.raise_for_status()
            data = resp.json()

            # Find best match by title similarity
            for paper in data.get("data", []):
                s2_title = (paper.get("title") or "").lower().strip()
                if self._title_match(clean_title, s2_title):
                    return self._parse_s2_result(paper, "semantic_scholar_title")

            return None
        except Exception as e:
            logger.debug("  S2 title search failed: %s", e)
            return None

    @staticmethod
    def _parse_s2_result(data: dict, source: str) -> Optional[Dict]:
        """Parse Semantic Scholar API result into enrichment dict."""
        authors = [a.get("name", "") for a in data.get("authors", []) if a.get("name")]
        abstract = data.get("abstract") or ""

        if not authors and not abstract:
            return None

        return {
            "authors": authors,
            "abstract": abstract,
            "enriched": True,
            "source": source,
        }

    # ---- CrossRef ----

    def _lookup_crossref_doi(self, doi: str) -> Optional[Dict]:
        """Look up paper by DOI on CrossRef."""
        api_url = f"{_CROSSREF_BASE}/{doi}"

        try:
            time.sleep(_API_DELAY)
            resp = self._session.get(api_url, timeout=10)
            if resp.status_code == 404:
                logger.debug("  CrossRef: DOI not found: %s", doi)
                return None
            resp.raise_for_status()
            data = resp.json()
            message = data.get("message", {})

            # Extract authors
            authors = []
            for author in message.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # Extract abstract (CrossRef provides it as XML-escaped text)
            abstract = message.get("abstract", "")
            if abstract:
                # Remove JATS XML tags
                abstract = re.sub(r'<[^>]+>', '', abstract).strip()

            if not authors and not abstract:
                return None

            return {
                "authors": authors,
                "abstract": abstract,
                "enriched": True,
                "source": "crossref_doi",
            }
        except Exception as e:
            logger.debug("  CrossRef lookup failed: %s", e)
            return None

    # ---- Title matching ----

    @staticmethod
    def _title_match(query_title: str, candidate_title: str) -> bool:
        """Check if two titles match closely enough."""
        # Normalize
        q = re.sub(r'[^\w\s]', '', query_title.lower()).strip()
        c = re.sub(r'[^\w\s]', '', candidate_title.lower()).strip()

        if not q or not c:
            return False

        # Check if one contains the other (handles truncated titles)
        if q in c or c in q:
            return True

        # Word overlap ratio
        q_words = set(q.split())
        c_words = set(c.split())
        if not q_words or not c_words:
            return False
        overlap = len(q_words & c_words) / max(len(q_words), len(c_words))
        return overlap > 0.7

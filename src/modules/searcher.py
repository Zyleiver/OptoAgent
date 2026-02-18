import requests
import feedparser
from typing import List, Optional
from datetime import datetime, timedelta
from models import Paper

class PaperSearcher:
    def __init__(self, exa_api_key: Optional[str] = None):
        self.exa_api_key = exa_api_key

    def search_active(self, query: str, limit: int = 5) -> List[Paper]:
        """
        Active search using Exa.ai (if key provided) or simulation.
        """
        if self.exa_api_key:
            return self._search_exa(query, limit)
        else:
            return self._search_simulated(query, limit)

    def monitor_sources(self, config_path: str = "tracking_sources.json") -> List[Paper]:
        """
        Monitor both RSS feeds (Journals) and Research Groups (Exa Site Search) defined in config.
        """
        import json
        import os
        
        if not os.path.exists(config_path):
            print(f"Config file {config_path} not found.")
            return []
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        papers = []
        
        # 1. Check RSS Feeds
        rss_feeds = config.get("rss_feeds", [])
        if rss_feeds:
            print(f"Checking {len(rss_feeds)} Journal RSS feeds...")
            papers.extend(self._check_rss_feeds(rss_feeds))
            
        # 2. Check Research Groups (via Exa)
        groups = config.get("research_groups", [])
        if self.exa_api_key and groups:
            print(f"Checking {len(groups)} Research Groups via Exa...")
            for group in groups:
                group_name = group.get("name")
                query = group.get("query")
                print(f"  - Tracking Group: {group_name}")
                # Use Exa to find recent content from these groups
                # Note: 'site:' queries are powerful here
                group_papers = self._search_exa(query, limit=3)
                for p in group_papers:
                    p.title = f"[{group_name}] {p.title}" # Tag the paper
                papers.extend(group_papers)
                
        return papers

    def _check_rss_feeds(self, rss_feeds: List[str]) -> List[Paper]:
        """
        Internal method to check RSS feeds.
        """
        new_papers = []
        # yesterday = datetime.now() - timedelta(days=1)
        
        for url in rss_feeds:
            try:
                feed = feedparser.parse(url)
                print(f"  - Parsed RSS {url}: {len(feed.entries)} entries found.")
                for entry in feed.entries[:3]: # Check latest 3 per feed
                    # In a real app, parse date properly.
                    # published = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                    # if published > yesterday: ...
                    
                    p = Paper(
                        title=entry.title,
                        authors=[a.name for a in entry.get('authors', [])] or ["Unknown"],
                        abstract=entry.get('summary', 'No abstract available.')[:500],
                        url=entry.link,
                        published_date=entry.get('published', '')
                    )
                    new_papers.append(p)
            except Exception as e:
                print(f"Failed to parse RSS {url}: {e}")
                
        return new_papers

    def _search_simulated(self, query: str, limit: int) -> List[Paper]:
        print(f"[Simulated] Searching for: {query}")
        return [
            Paper(
                title=f"Simulated Result for {query}",
                authors=["AI Researcher"],
                abstract="This is a placeholder result because no EXA_API_KEY was provided.",
                url="http://example.com/simulated",
                published_date="2024-01-01"
            )
        ] * limit

    def _search_exa(self, query: str, limit: int) -> List[Paper]:
        print(f"[Exa] Searching for: {query}")
        url = "https://api.exa.ai/search"
        headers = {
            "x-api-key": self.exa_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "numResults": limit,
            "contents": {
                "text": True 
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for result in data.get("results", []):
                p = Paper(
                    title=result.get("title", "No Title"),
                    authors=result.get("author", "").split(", ") if result.get("author") else [],
                    abstract=result.get("text", "")[:500] + "...", # Truncate content as abstract
                    url=result.get("url"),
                    published_date=result.get("publishedDate")
                )
                papers.append(p)
            return papers
            
        except Exception as e:
            print(f"[Exa] Search failed: {e}")
            return []

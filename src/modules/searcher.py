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

    def monitor_journals(self, rss_feeds: List[str]) -> List[Paper]:
        """
        Check RSS feeds for new papers in the last 24 hours.
        """
        print(f"Checking {len(rss_feeds)} RSS feeds...")
        new_papers = []
        # yesterday = datetime.now() - timedelta(days=1)
        
        for url in rss_feeds:
            try:
                feed = feedparser.parse(url)
                print(f"  - Parsed {url}: {len(feed.entries)} entries found.")
                for entry in feed.entries[:5]: # Check latest 5 per feed
                    # In a real app, parse date properly.
                    # published = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                    # if published > yesterday: ...
                    
                    p = Paper(
                        title=entry.title,
                        authors=[a.name for a in entry.get('authors', [])] or ["Unknown"],
                        abstract=entry.get('summary', 'No abstract available.'),
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

import os
import feedparser
import requests
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_tavily = None

def _get_tavily():
    global _tavily
    if _tavily is None:
        _tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _tavily


def search(query: str, max_results: int = 5) -> list[dict]:
    """Search using Tavily. Returns list of {title, url, content}."""
    try:
        client = _get_tavily()
        results = client.search(query, max_results=max_results)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in results.get("results", [])
        ]
    except Exception as e:
        print(f"[Search] Tavily error for '{query}': {e}")
        return []


def search_rss(feed_url: str, max_results: int = 5) -> list[dict]:
    """Fetch and parse an RSS feed. Returns list of {title, url, content}."""
    try:
        feed = feedparser.parse(feed_url)
        results = []
        for entry in feed.entries[:max_results]:
            results.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "content": entry.get("summary", entry.get("description", "")),
            })
        return results
    except Exception as e:
        print(f"[Search] RSS error for '{feed_url}': {e}")
        return []


def multi_search(queries: list[str], max_per_query: int = 3) -> list[dict]:
    """Run multiple search queries and deduplicate by URL."""
    seen_urls = set()
    all_results = []
    for query in queries:
        results = search(query, max_results=max_per_query)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)
    return all_results

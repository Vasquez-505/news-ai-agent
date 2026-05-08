import feedparser


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

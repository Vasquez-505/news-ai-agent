from search.searcher import multi_search
from llm.provider import get_llm

QUERIES = [
    "top world news today breaking international",
    "major geopolitical events this week",
    "global crisis conflict humanitarian news today",
]

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant.

Based on the search results below, write the WORLD NEWS section of today's briefing.

RULES:
- Maximum 5 bullet points
- Each bullet: bold the subject at the start (e.g. **Gaza:**), then state the fact AND briefly explain what it means
- 1-2 sentences per bullet
- No soft news, no celebrity, no sport
- End with a single line: "Why it matters: [one sentence on broader impact]"
- Tone: intelligent, neutral, factual. No hype.
- For each bullet, note the source in brackets at the end e.g. [Reuters]

SEARCH RESULTS:
{results}

Write the World News section now:"""


def fetch() -> dict:
    llm = get_llm()
    results = multi_search(QUERIES, max_per_query=3)

    results_text = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(results=results_text)
    summary = llm.generate(prompt)

    return {
        "id": "general_world_news",
        "title": "🌍 World News",
        "content": summary,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

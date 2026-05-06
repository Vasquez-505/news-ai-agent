from search.searcher import multi_search
from llm.provider import get_llm

QUERIES = [
    "new AI model released this week OpenAI Anthropic Google DeepMind xAI Meta Mistral DeepSeek",
    "new AI product launch this week Google OpenAI Microsoft Meta app feature API",
    "AI productivity tools launched this week Cursor Notion Figma Adobe Perplexity",
    "AI workplace automation news this week",
]

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant.

Based on the search results below, write the AI & PRODUCTIVITY section of today's briefing.

RULES:
- Maximum 5 bullet points
- Prioritize SHIPPED products over announcements. Prioritize practical impact over research papers.
- Each bullet: bold the subject at the start (e.g. **OpenAI:**), state what launched AND what it means in practice
- 1-2 sentences per bullet
- End with a single line: "Why it matters: [one sentence]"
- Tone: intelligent, factual, no hype
- For each bullet, note the source in brackets at the end e.g. [TechCrunch]

SEARCH RESULTS:
{results}

Write the AI & Productivity section now:"""


def fetch() -> dict:
    llm = get_llm()
    results = multi_search(QUERIES, max_per_query=3)

    results_text = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(results=results_text)
    summary = llm.generate(prompt)

    return {
        "id": "ai_productivity",
        "title": "⚡ AI & Productivity",
        "content": summary,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

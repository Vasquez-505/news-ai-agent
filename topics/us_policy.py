from search.searcher import multi_search
from llm.provider import get_llm
from datetime import datetime

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant.

Based on the search results below, write the UNITED STATES POLICY section of today's briefing.

RULES:
- Only include signed legislation, signed executive orders, or enacted regulatory changes
- Maximum 5 bullet points
- Each bullet: bold the subject, name the action, describe its CONCRETE content (agencies involved, what is mandated, what changes), explain the implication
- Balanced and factual — no political framing, just what was enacted and what it means
- End with: "Why it matters: [one sentence]"
- Tone: neutral, factual
- Note the source in brackets e.g. [White House]

SEARCH RESULTS:
{results}

Write the US Policy section now:"""


def fetch() -> dict:
    llm = get_llm()
    month_year = datetime.now().strftime("%B %Y")

    queries = [
        f"executive order signed {month_year}",
        f"US law signed Congress {month_year}",
        f"US regulation change enacted {month_year}",
        f"White House policy action {month_year}",
        f"Federal Register new rule {month_year}",
    ]

    results = multi_search(queries, max_per_query=3)

    results_text = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(results=results_text)
    summary = llm.generate(prompt)

    return {
        "id": "us_policy",
        "title": "🇺🇸 United States Policy",
        "content": summary,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

from search.searcher import multi_search
from llm.provider import get_llm
from datetime import datetime

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant. Pedro is based in Portugal.

Based on the search results below, write the PORTUGAL POLICY & LAW section of today's briefing.

RULES:
- Only include laws, regulations, or policies that have been SIGNED, APPROVED, or are ENTERING INTO FORCE
- No proposals, no debates, no speculation
- Maximum 5 bullet points
- Each bullet: bold the subject, name the law/measure, describe its CONCRETE provisions (thresholds, who is affected, what changes), then explain practical impact
- Do NOT just name a law — describe what it actually does
- End with: "Why it matters: [one sentence]"
- Tone: neutral, factual, clear
- For each bullet, note the source in brackets e.g. [Diario da Republica]

SEARCH RESULTS:
{results}

If there are no relevant approved laws or policies this week, say so briefly and note what to watch for.

Write the Portugal Policy section now:"""


def fetch() -> dict:
    llm = get_llm()
    month_year = datetime.now().strftime("%B %Y")

    queries = [
        f"Portugal nova lei aprovada {month_year}",
        f"Assembleia da Republica aprovacao {month_year}",
        f"Governo portugues medidas aprovadas {month_year}",
        f"Portugal tax changes law {month_year}",
        f"Diario da Republica new laws {month_year}",
    ]

    results = multi_search(queries, max_per_query=3)

    results_text = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(results=results_text)
    summary = llm.generate(prompt)

    return {
        "id": "portugal_policy",
        "title": "🇵🇹 Portugal Policy & Law",
        "content": summary,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

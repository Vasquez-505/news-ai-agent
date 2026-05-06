from search.searcher import multi_search
from llm.provider import get_llm
from datetime import datetime

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant. Pedro is based in Portugal.

Based on the search results below, write the EUROPEAN UNION POLICY section of today's briefing.

RULES:
- Only include regulations, directives, or decisions that have been FORMALLY APPROVED or are ENTERING INTO FORCE
- Maximum 5 bullet points
- Each bullet: bold the subject, name the regulation, describe its CONCRETE requirements (obligations, thresholds, timelines, enforcement)
- Do NOT just name a regulation — describe what it actually requires
- Flag anything with direct relevance to Portugal or Portuguese citizens
- End with: "Why it matters: [one sentence]"
- Tone: neutral, factual
- Note the source in brackets e.g. [EUR-Lex]

SEARCH RESULTS:
{results}

Write the EU Policy section now:"""


def fetch() -> dict:
    llm = get_llm()
    month_year = datetime.now().strftime("%B %Y")

    queries = [
        f"EU regulation approved {month_year}",
        f"European Commission directive {month_year}",
        f"European Parliament vote approved {month_year}",
        f"EU law entering into force {month_year}",
        "EU regulation Portugal impact citizens businesses",
    ]

    results = multi_search(queries, max_per_query=3)

    results_text = "\n\n".join(
        f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results
    )

    prompt = PROMPT_TEMPLATE.format(results=results_text)
    summary = llm.generate(prompt)

    return {
        "id": "eu_policy",
        "title": "🇪🇺 European Union Policy",
        "content": summary,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }

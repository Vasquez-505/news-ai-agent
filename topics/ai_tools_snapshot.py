from datetime import datetime
from llm.provider import get_llm

PEDRO_TOOLS = {
    "Coding / Agents":       "Claude Code (Anthropic)",
    "Excel / Spreadsheets":  "Claude.ai",
    "Presentations":         "Claude.ai",
    "Documents / Word":      "Claude.ai",
    "LaTeX / Overleaf":      "Overleaf + Claude.ai",
    "Knowledge Management":  "Notion",
    "Image Generation":      "Midjourney / DALL-E",
    "Research / Web Search": "Perplexity",
    "Transcription / Audio": "Whisper / Otter",
    "Task Automation":       "Make / Zapier",
}

PROMPT = """<role>
You are Pedro's AI tools advisor. Pedro is a technically sophisticated user in Portugal who uses AI tools daily for coding, research, and productivity. He prioritises free or already-subscribed tools and wants honest, actionable comparisons.
Pedro has Claude Pro — full access to all Claude models and Claude Code.
</role>

<task>
Today is {date}. Do two things:
1. Using the search results above AND the AI news context below, identify any AI tool releases, pricing changes, or significant capability updates from the last 24 hours.
2. Generate the AI TOOLS SNAPSHOT — comparing Pedro's current tools against today's best alternatives.
</task>

<todays_ai_news>
{ai_productivity_context}
</todays_ai_news>

<pedro_current_tools>
{tools_list}
</pedro_current_tools>

<output_format>
First, write the table header exactly as shown:
AI TOOLS SNAPSHOT
Category | Pedro uses | Best today | Alternative | Cost/Plan | Migration effort | Switch? | Reason

Then write one pipe-separated row per category. Use these exact Switch? values:
- Optimal -> Pedro is already on the best tool
- Consider -> Worth evaluating, not urgent
- Upgrade -> Clear improvement available, should switch
- Not using -> Category not yet covered by AI

Keep Motivo to one sentence max. Be specific about pricing (free tier, $X/month).
If something shipped today (from the AI news context above) changes a recommendation, say so explicitly in Motivo.

After the table, write exactly:
Takeaway: [One sentence — the single most actionable change Pedro could make today, informed by what actually shipped]
</output_format>

<quality_rules>
- Base recommendations on tools actually available and publicly released as of today
- Prioritise free tiers and tools Pedro already pays for (Claude Pro = access to all Claude models)
- Do not recommend tools requiring enterprise contracts or unavailable in Portugal/EU
- Be honest: if Pedro's current tool is genuinely the best, say Optimal
- Motivo must be specific: cite actual release names, benchmark numbers, or pricing
- If today's AI news changes any recommendation, that row takes priority
</quality_rules>"""


SEARCH_QUERIES = [
    "AI tool app pricing update release today 2026",
    "ChatGPT Claude Gemini Perplexity Cursor update feature today",
    "new AI productivity tool launched today comparison",
]


def fetch(ai_productivity_content: str = "") -> dict:
    llm = get_llm()
    tools_list = "\n".join(f"- {cat}: {tool}" for cat, tool in PEDRO_TOOLS.items())
    context = ai_productivity_content.strip() or "No AI news available for today."

    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        tools_list=tools_list,
        ai_productivity_context=context,
    )
    content, sources = llm.generate_with_search(prompt, search_queries=SEARCH_QUERIES)
    return {
        "id": "ai_tools_snapshot",
        "title": "AI Tools Snapshot",
        "content": content,
        "sources": sources,
    }

from datetime import datetime
from llm.provider import get_llm

PEDRO_TOOLS = {
    "Código / Agentes":      "Claude Code (Anthropic)",
    "Excel / Spreadsheets":  "Manual + ChatGPT",
    "Presentations":         "Manual + ChatGPT",
    "Documents / Word":      "Manual + ChatGPT",
    "LaTeX / Overleaf":      "Overleaf + ChatGPT",
    "Knowledge Management":  "Notion",
    "Image Generation":      "Midjourney / DALL-E",
    "Research / Web Search": "Perplexity",
    "Transcription / Audio": "Whisper / Otter",
    "Task Automation":       "Make / Zapier",
}

PROMPT = """<role>
You are Pedro's AI tools advisor. Pedro is a technically sophisticated user in Portugal who uses AI tools daily for coding, research, and productivity. He prioritises free or already-subscribed tools and wants honest, actionable comparisons.
</role>

<task>
Today is {date}. Generate the AI TOOLS SNAPSHOT — a daily comparison of Pedro's current tools against today's best alternatives, informed by the latest AI landscape.
</task>

<pedro_current_tools>
{tools_list}
</pedro_current_tools>

<output_format>
First, write the table header exactly as shown:
AI TOOLS SNAPSHOT
Categoria | Pedro usa | Melhor atual | Alternativa | Custo/Plano | Esforço migração | Switch? | Motivo

Then write one pipe-separated row per category. Use these exact Switch? values:
- Optimal → Pedro is already on the best tool
- Consider → Worth evaluating, not urgent
- Upgrade → Clear improvement available, should switch
- Not using → Category not yet covered by AI

Keep Motivo to one sentence max. Be specific about pricing (free tier, $X/month).

After the table, write exactly:
Takeaway: [One sentence — the single most actionable change Pedro could make today to improve his AI toolkit]
</output_format>

<quality_rules>
- Base recommendations on tools actually available and publicly released as of today
- Prioritise free tiers and tools Pedro already pays for (Claude Pro = access to Claude models)
- Consider that Pedro uses Claude Code — he has access to Anthropic's ecosystem
- Do not recommend tools that require enterprise contracts or are not available in Portugal/EU
- Be honest: if Pedro's current tool is genuinely the best, say Optimal
- Motivo must be specific: "Claude Sonnet 4.5 now matches GPT-4o on coding benchmarks at no extra cost" not "better performance"
</quality_rules>"""


def fetch() -> dict:
    llm = get_llm()
    tools_list = "\n".join(f"- {cat}: {tool}" for cat, tool in PEDRO_TOOLS.items())
    prompt = PROMPT.format(
        date=datetime.now().strftime("%A, %B %d, %Y"),
        tools_list=tools_list,
    )
    content = llm.generate(prompt)
    return {
        "id": "ai_tools_snapshot",
        "title": "🛠️ AI Tools Snapshot",
        "content": content,
        "sources": [],
    }

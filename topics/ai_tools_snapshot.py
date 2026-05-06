from llm.provider import get_llm
from datetime import datetime

PEDRO_TOOLS = """
Pedro's current tools (from AI_AGENTES_AUTONOMOS.txt context):
- Codigo / Agentes: Claude Code (Anthropic)
- Excel: Manual / ChatGPT
- PowerPoint: Manual / ChatGPT
- Word: Manual / ChatGPT
- LaTeX / Overleaf: Overleaf + ChatGPT
- Knowledge Management: Notion
- Geracao de imagens: Midjourney / DALL-E
- Pesquisa / Web search: Perplexity
- Transcricao / Audio: Whisper / Otter
- Automacao de tarefas: Make / Zapier
"""

PROMPT_TEMPLATE = """You are Pedro's morning intelligence briefing assistant.

Today is {date}. Based on the latest AI releases and market knowledge, generate the AI TOOLS SNAPSHOT table.

Pedro's current tools:
{pedro_tools}

Generate a table comparing Pedro's tools against current best-in-class options.
Use this exact format (plain text, pipe-separated):

AI TOOLS SNAPSHOT
Categoria | Pedro usa | Melhor atual | Alternativa | Custo/Plano | Esfoco migracao | Switch? | Motivo
Codigo / Agentes | ... | ... | ... | ... | Baixo/Medio/Alto | Optimal/Consider/Upgrade/Not using | ...
Excel | ... | ... | ... | ... | ... | ... | ...
PowerPoint | ... | ... | ... | ... | ... | ... | ...
Word | ... | ... | ... | ... | ... | ... | ...
LaTeX / Overleaf | ... | ... | ... | ... | ... | ... | ...
Knowledge Management | ... | ... | ... | ... | ... | ... | ...
Geracao de imagens | ... | ... | ... | ... | ... | ... | ...
Pesquisa / Web search | ... | ... | ... | ... | ... | ... | ...
Transcricao / Audio | ... | ... | ... | ... | ... | ... | ...
Automacao de tarefas | ... | ... | ... | ... | ... | ... | ...

End with: "Takeaway: [1 sentence — most actionable change Pedro could make today]"

Be specific and accurate based on what actually exists today. Keep Motivo to 1 sentence."""


def fetch() -> dict:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(
        date=datetime.now().strftime("%B %d, %Y"),
        pedro_tools=PEDRO_TOOLS,
    )
    summary = llm.generate(prompt)

    return {
        "id": "ai_tools_snapshot",
        "title": "🛠️ AI Tools Snapshot",
        "content": summary,
        "sources": [],
    }

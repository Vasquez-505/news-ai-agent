from datetime import datetime
from llm.provider import get_llm

PROMPT = """<role>
You are Pedro's morning intelligence briefing assistant. Pedro works with AI tools daily (Claude Code, Notion, Perplexity, Midjourney) and wants to know what actually shipped — not what was announced or rumoured.
</role>

<task>
Today is {date}. Search for and write the AI & PRODUCTIVITY section of this morning's briefing.
Find the most significant AI model releases and product launches from the last 48 hours.
</task>

<selection_criteria>
PRIORITISE (in this order):
1. New AI models released by major labs (Anthropic, OpenAI, Google DeepMind, Meta, Mistral, xAI, DeepSeek)
2. Major product launches or significant feature releases (not minor updates)
3. AI productivity tool updates that change workflows (Cursor, Notion, Figma, Adobe, Perplexity, etc.)
4. Significant open-source model releases on Hugging Face

EXCLUDE:
- Research papers not yet deployed
- Vague announcements without a release date or shipping product
- Minor UI tweaks or bug fixes
- Speculation about upcoming releases

SOURCE PREFERENCE: Official lab blogs (anthropic.com, openai.com, deepmind.google), Hugging Face blog, TechCrunch AI, The Batch (DeepLearning.AI)
</selection_criteria>

<output_format>
Write 3–5 bullet points. Exactly this structure for each:

• **[Lab or Product Name]:** [What shipped — 1 sentence describing the specific capability or release]. [Practical impact — 1 sentence on what this actually changes for someone using AI tools today]. [Source Name]

After all bullets, write exactly one line:
Why it matters: [One sentence on the most significant shift in the AI landscape today]
</output_format>

<quality_rules>
- SHIPPED beats ANNOUNCED — if it is not publicly available, it does not belong here
- Be specific: name the model version, the capability, the benchmark improvement, the price
- Practical impact must be concrete ("saves 2 hours of manual work") not vague ("improves productivity")
- If nothing significant shipped in the last 48 hours, say so briefly and note what to watch for
- Maximum 5 bullets — quality over quantity
</quality_rules>"""


SEARCH_QUERIES = [
    "AI model release today OpenAI Anthropic Google DeepMind Meta",
    "new AI tool product launch shipped today 2026",
    "Cursor Notion Perplexity AI feature update release today",
]


def fetch() -> dict:
    llm = get_llm()
    prompt = PROMPT.format(date=datetime.now().strftime("%A, %B %d, %Y"))
    content, sources = llm.generate_with_search(prompt, search_queries=SEARCH_QUERIES)
    return {
        "id": "ai_productivity",
        "title": "⚡ AI & Productivity",
        "content": content,
        "sources": sources,
    }

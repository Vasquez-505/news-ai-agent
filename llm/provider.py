import logging
import os
import time
import yaml
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

_RETRY_ATTEMPTS = 3
_RETRY_WAIT = 35  # seconds — just over the 429 retry_delay Gemini returns

# Gemini 2.5 Flash is used exclusively for news synthesis (Tavily context + generation).
# It has 250 free RPD and produces noticeably better quality briefings than Gemma.
# The configured model (Gemma) handles plain generation and all chat calls,
# where quota matters more than peak quality.
_SEARCH_SYNTHESIS_MODEL = "gemini-2.5-flash"


def _call_with_retry(fn):
    """Call fn(), retrying up to _RETRY_ATTEMPTS times on 429 quota errors."""
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            return fn()
        except Exception as e:
            if "429" in str(e) and attempt < _RETRY_ATTEMPTS:
                logger.warning("Rate limited (429), waiting %ds before retry %d/%d",
                               _RETRY_WAIT, attempt, _RETRY_ATTEMPTS - 1)
                time.sleep(_RETRY_WAIT)
            else:
                raise


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_llm():
    config = load_config()
    provider = config["llm"]["provider"]
    model = config["llm"]["model"]

    if provider == "gemini":
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return GeminiProvider(model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class GeminiProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self._synthesis_model = genai.GenerativeModel(_SEARCH_SYNTHESIS_MODEL)

    def generate(self, prompt: str) -> str:
        """Plain generation using the configured model (Gemma)."""
        response = _call_with_retry(lambda: self.model.generate_content(prompt))
        return response.text.strip()

    def generate_with_search(self, prompt: str, search_queries: list[str] | None = None) -> tuple[str, list[dict]]:
        """
        Fetches live context via Tavily, then synthesises with gemini-2.5-flash.
        Falls back to plain generate() on any failure.
        Returns (text, sources).
        """
        tavily_key = os.getenv("TAVILY_API_KEY")
        if search_queries and tavily_key:
            return self._tavily_then_synthesise(prompt, search_queries)

        # No Tavily available — degrade gracefully to plain generate
        logger.warning("No Tavily key or search_queries; generating without live context")
        return self.generate(prompt), []

    def _tavily_then_synthesise(self, prompt: str, search_queries: list[str]) -> tuple[str, list[dict]]:
        """Search with Tavily, inject results, synthesise with gemini-2.5-flash."""
        try:
            from search.searcher import multi_search
            results = multi_search(search_queries, max_per_query=4)

            if not results:
                logger.warning("Tavily returned no results; generating without live context")
                return self.generate(prompt), []

            context_block = "\n\n".join(
                f"[{i + 1}] {r['title']}\nURL: {r['url']}\n{r['content'][:500]}"
                for i, r in enumerate(results[:12])
            )
            augmented_prompt = (
                f"<search_results>\n{context_block}\n</search_results>\n\n"
                f"Use the search results above as your primary source for today's news. "
                f"Only cite facts that appear in those results — do not invent sources. "
                f"Output only the final briefing text — no internal reasoning, no self-correction, no meta-commentary.\n\n"
                + prompt
            )

            # Try gemini-2.5-flash first; fall back to configured model if quota is hit
            try:
                response = _call_with_retry(
                    lambda: self._synthesis_model.generate_content(augmented_prompt)
                )
            except Exception as e:
                logger.warning(
                    "%s synthesis failed (%s); falling back to %s",
                    _SEARCH_SYNTHESIS_MODEL, e, self.model_name,
                )
                response = _call_with_retry(
                    lambda: self.model.generate_content(augmented_prompt)
                )

            sources = [{"title": r["title"], "url": r["url"]} for r in results if r.get("url")]
            return response.text.strip(), sources

        except Exception as e:
            logger.warning("Tavily search failed (%s); generating without live context", e)
            return self.generate(prompt), []

    def chat(self, history: list[dict], message: str, system: str = "") -> str:
        """
        Multi-turn chat using the configured model (Gemma) — high quota, good for Q&A.
        history: list of {"role": "user"|"model", "parts": [str]} dicts.
        """
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system if system else None,
        )
        session = model.start_chat(history=history)
        response = _call_with_retry(lambda: session.send_message(message))
        return response.text.strip()

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

    def generate(self, prompt: str) -> str:
        """Single-turn generation without search."""
        response = _call_with_retry(lambda: self.model.generate_content(prompt))
        return response.text.strip()

    def generate_with_search(self, prompt: str) -> tuple[str, list[dict]]:
        """
        Single-turn generation with Google Search grounding.
        Falls back to plain generate() if grounding fails.
        Returns (text, sources) where sources is a list of {title, url} dicts.
        """
        try:
            model = genai.GenerativeModel(
                self.model_name,
                tools=[{"google_search": {}}],
            )
            response = _call_with_retry(lambda: model.generate_content(prompt))
            text = response.text.strip()

            sources = []
            try:
                chunks = response.candidates[0].grounding_metadata.grounding_chunks
                seen = set()
                for chunk in chunks:
                    if hasattr(chunk, "web") and chunk.web:
                        url = chunk.web.uri or ""
                        title = chunk.web.title or url
                        if url and url not in seen:
                            seen.add(url)
                            sources.append({"title": title, "url": url})
            except (AttributeError, IndexError):
                pass

            if not text:
                raise ValueError("Grounding returned empty response")

            return text, sources

        except Exception as e:
            logger.warning("Grounding failed (%s), falling back to plain generate", e)
            return self.generate(prompt), []

    def chat(self, history: list[dict], message: str, system: str = "") -> str:
        """
        Multi-turn chat using Gemini's native ChatSession.
        history: list of {"role": "user"|"model", "parts": [str]} dicts.
        system: optional system instruction prepended to the first user turn.
        """
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system if system else None,
        )
        # Convert history to Gemini format (already compatible)
        session = model.start_chat(history=history)
        response = _call_with_retry(lambda: session.send_message(message))
        return response.text.strip()

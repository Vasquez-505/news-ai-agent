import logging
import os
import time
import yaml
from google import genai
from google.genai import types
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

_RETRY_ATTEMPTS = 3
_RETRY_WAIT = 35  # seconds — just over the 429 retry_delay Gemini returns

# Gemini 2.5 Flash handles all generate_with_search() calls — native Google
# Search grounding means it searches Google's full index and synthesises in
# one call, no external search API needed.
# The configured model (Gemma) handles generate() and chat() — higher quota,
# no grounding needed for plain text generation and bot conversations.
_SEARCH_MODEL = "gemini-2.5-flash"


def _call_with_retry(fn):
    """Call fn(), retrying on 429 (quota) and 500 (transient server) errors."""
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            is_last = attempt >= _RETRY_ATTEMPTS
            if "429" in msg and not is_last:
                logger.warning("Rate limited (429), waiting %ds before retry %d/%d",
                               _RETRY_WAIT, attempt, _RETRY_ATTEMPTS - 1)
                time.sleep(_RETRY_WAIT)
            elif "500" in msg and not is_last:
                logger.warning("Server error (500), waiting 5s before retry %d/%d",
                               attempt, _RETRY_ATTEMPTS - 1)
                time.sleep(5)
            else:
                raise


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_llm():
    config = load_config()
    provider = config["llm"]["provider"]
    model    = config["llm"]["model"]

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider(model, api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class GeminiProvider:
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Plain generation using the configured model (Gemma)."""
        response = _call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        )
        return response.text.strip()

    def generate_with_search(self, prompt: str) -> tuple[str, list[dict]]:
        """
        Generate with native Google Search grounding via Gemini 2.5 Flash.
        Gemini searches Google's full index as part of generation — no external
        search API needed. Falls back to plain generate() on any failure.
        Returns (text, sources).
        """
        try:
            response = _call_with_retry(
                lambda: self.client.models.generate_content(
                    model=_SEARCH_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                )
            )
            text = response.text.strip()
            if not text:
                raise ValueError("Empty response from grounding")

            sources = []
            try:
                chunks = response.candidates[0].grounding_metadata.grounding_chunks
                seen = set()
                for chunk in chunks:
                    if hasattr(chunk, "web") and chunk.web:
                        url   = chunk.web.uri   or ""
                        title = chunk.web.title or url
                        if url and url not in seen:
                            seen.add(url)
                            sources.append({"title": title, "url": url})
            except (AttributeError, IndexError):
                pass

            return text, sources

        except Exception as e:
            logger.warning("Grounding failed (%s); falling back to plain generate", e)
            return self.generate(prompt), []

    def chat(self, history: list[dict], message: str, system: str = "") -> str:
        """
        Multi-turn chat using the configured model (Gemma).
        history: list of {"role": "user"|"model", "parts": [str]} dicts.
        """
        chat_history = [
            types.Content(
                role=msg["role"],
                parts=[types.Part(text=p) for p in msg["parts"]],
            )
            for msg in history
        ]
        config = types.GenerateContentConfig(
            system_instruction=system if system else None,
        )
        chat_session = self.client.chats.create(
            model=self.model_name,
            config=config,
            history=chat_history,
        )
        response = _call_with_retry(lambda: chat_session.send_message(message))
        return response.text.strip()

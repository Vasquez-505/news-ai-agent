import os
import yaml
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

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
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_with_search(self, prompt: str) -> str:
        model = genai.GenerativeModel(
            self.model.model_name,
            tools=[{"google_search": {}}]
        )
        response = model.generate_content(prompt)
        return response.text.strip()

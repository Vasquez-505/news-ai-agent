import os
import asyncio
import yaml
import edge_tts
from dotenv import load_dotenv

load_dotenv()

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


async def _edge_tts_generate(text: str, output_path: str, voice: str, rate: str, pitch: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def generate_audio(text: str, output_path: str) -> str:
    """Generate TTS audio file. Returns path to the .mp3 file."""
    config = load_config()
    provider = config["tts"]["provider"]

    if provider == "edge-tts":
        voice = config["tts"]["voice"]
        rate = config["tts"].get("rate", "-5%")
        pitch = config["tts"].get("pitch", "-5st")
        # Run in a new thread's event loop to avoid conflicts with an existing loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                _edge_tts_generate(text, output_path, voice, rate, pitch),
            )
            future.result()
        return output_path

    elif provider == "elevenlabs":
        return _elevenlabs_generate(text, output_path)

    else:
        raise ValueError(f"Unsupported TTS provider: {provider}")


def _elevenlabs_generate(text: str, output_path: str) -> str:
    import requests
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8},
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path

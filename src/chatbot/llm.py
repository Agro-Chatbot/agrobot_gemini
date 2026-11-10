from google import genai

from . import config

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("Falta GEMINI_API_KEY en el .env.")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client
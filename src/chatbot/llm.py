import anthropic

from . import config

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("Falta ANTHROPIC_API_KEY en el .env.")
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client

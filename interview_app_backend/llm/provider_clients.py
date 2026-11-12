try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - keeps tests runnable without the optional dependency
    class OpenAI:  # type: ignore[too-many-ancestors]
        pass

from config.settings import GOOGLE_API_KEY, XAI_API_KEY


def create_google_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta")


def get_google_client() -> OpenAI:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set")
    return create_google_client(GOOGLE_API_KEY)


def create_grok_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def get_grok_client() -> OpenAI:
    if not XAI_API_KEY:
        raise ValueError("XAI_API_KEY is not set")
    return create_grok_client(XAI_API_KEY)

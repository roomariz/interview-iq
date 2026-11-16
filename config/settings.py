import os
from pathlib import Path

from dotenv import dotenv_values
from dotenv import load_dotenv


APP_TITLE = "Interview Practice App"
TEMPERATURE = 0.7
DEFAULT_MODEL = "google/gemma-4-31b-it:free"


def _env_flag(name: str, default: bool = False) -> bool:
    value = str(ENV_VALUES.get(name) or os.getenv(name) or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}

ALLOWED_PROVIDERS = ["openrouter", "grok", "google"]
BLOCK_DATA_COLLECTING = True

PRIMARY_PROVIDER = "open-router"
FALLBACK_PROVIDERS = ["grok", "google"]

QUESTION_GENERATION_PROVIDERS = ["open-router"]
QUESTION_GENERATION_FALLBACKS = []
FREE_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-12b-it:free",
]
FREE_EVAL_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-12b-it:free",
]
QUESTION_GENERATION_FALLBACK_CHAIN = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-12b-it:free",
    "openai/gpt-5-nano",
]
FALLBACK_CHAIN = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-12b-it:free",
    "openai/gpt-5-nano",
]
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)
ENV_VALUES = dotenv_values(ENV_PATH)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", ENV_VALUES.get("OPENROUTER_API_KEY", "")).strip()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", ENV_VALUES.get("GOOGLE_API_KEY", "")).strip()
XAI_API_KEY = os.getenv("XAI_API_KEY", ENV_VALUES.get("XAI_API_KEY", "")).strip()
IS_FREE_MODE = _env_flag("IS_FREE_MODE", True)
CONFIGURED_MODEL_NAME = str(ENV_VALUES.get("MODEL_NAME") or os.getenv("MODEL_NAME") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
MODEL_NAME = DEFAULT_MODEL if IS_FREE_MODE else CONFIGURED_MODEL_NAME
LLM_TIMEOUT = int(ENV_VALUES.get("LLM_TIMEOUT") or os.getenv("LLM_TIMEOUT") or 60)

# Project cloud credentials and host take precedence over inherited Ollama settings.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", ENV_VALUES.get("LLM_PROVIDER") or "open-router").strip().lower()
if LLM_PROVIDER == "openrouter":
    LLM_PROVIDER = "open-router"
if LLM_PROVIDER not in {"open-router", "ollama", "grok", "google"}:
    raise ValueError("LLM_PROVIDER must be open-router, openrouter, ollama, grok or google")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", ENV_VALUES.get("GOOGLE_MODEL") or "gemini-3.5-flash-lite").strip()
GROK_MODEL = os.getenv("GROK_MODEL", ENV_VALUES.get("GROK_MODEL") or "grok-4.3").strip()
OLLAMA_API_KEY = str(ENV_VALUES.get("OLLAMA_API_KEY") or os.getenv("OLLAMA_API_KEY") or "").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", ENV_VALUES.get("OLLAMA_MODEL") or "gemma4:cloud").strip()
# A local Ollama installation may already export OLLAMA_HOST for its own server.
OLLAMA_HOST = str(ENV_VALUES.get("OLLAMA_HOST") or os.getenv("OLLAMA_HOST") or "https://ollama.com").strip()
OLLAMA_FALLBACK_TO_OPENROUTER = os.getenv(
    "OLLAMA_FALLBACK_TO_OPENROUTER", ENV_VALUES.get("OLLAMA_FALLBACK_TO_OPENROUTER") or "false"
).strip().lower() in {"1", "true", "yes", "on"}
OPENROUTER_MODEL_NAME = MODEL_NAME
PRIMARY_PROVIDER = LLM_PROVIDER
if LLM_PROVIDER == "ollama":
    MODEL_NAME = OLLAMA_MODEL
elif LLM_PROVIDER == "grok":
    MODEL_NAME = GROK_MODEL
elif LLM_PROVIDER == "google":
    MODEL_NAME = GOOGLE_MODEL

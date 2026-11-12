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

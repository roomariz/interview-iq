from __future__ import annotations

import config.settings as settings

FREE_ROUTED_MODEL = "google/gemma-4-31b-it:free"

MODEL_CONFIG = {
    "paid": {
        "strict_json": True,
        "max_questions": 10,
        "prompt_style": "strict",
        "retry_limit": 2,
        "question_count": 5,
        "call_delay_seconds": 0,
        "allow_free_model_fallback": False,
        "routed_model": "",
    },
    "free": {
        "strict_json": False,
        "max_questions": 3,
        "prompt_style": "simple",
        "retry_limit": 1,
        "question_count": 3,
        "call_delay_seconds": 0,
        "allow_free_model_fallback": True,
        "routed_model": FREE_ROUTED_MODEL,
    },
}


def is_free_model(model_name: str | None) -> bool:
    name = str(model_name or "").strip().lower()
    if not name:
        return False
    return name.endswith(":free") or name in {item.lower() for item in settings.FREE_MODELS}


def get_model_profile(model_name: str | None) -> dict[str, object]:
    profile_key = "free" if is_free_model(model_name) else "paid"
    return dict(MODEL_CONFIG[profile_key])


def get_routed_model_name(model_name: str | None) -> str:
    profile = get_model_profile(model_name)
    routed_model = str(profile.get("routed_model", "")).strip()
    if routed_model:
        return routed_model
    return str(model_name or "").strip()


def _task_family(task: str | None) -> str:
    cleaned = str(task or "").strip().lower()
    if cleaned.startswith("evaluation."):
        return "evaluation"
    if cleaned.startswith("question_generation."):
        return "question_generation"
    return "general"


def get_fallback_chain(model_name: str | None, task: str | None = None) -> list[str]:
    candidate = str(model_name or "").strip()
    if not is_free_model(candidate):
        return [candidate] if candidate else []

    family = _task_family(task)
    if family == "evaluation":
        chain = list(settings.FREE_EVAL_MODELS)
    elif family == "question_generation":
        chain = list(settings.QUESTION_GENERATION_FALLBACK_CHAIN)
    else:
        chain = [candidate, *settings.FALLBACK_CHAIN]

    fallbacks: list[str] = []
    seen: set[str] = set()
    for item in chain:
        cleaned = str(item or "").strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        fallbacks.append(cleaned)
    if family == "general" and candidate and candidate.lower() not in seen:
        fallbacks.insert(0, candidate)
    return fallbacks


def get_free_model_fallbacks(model_name: str | None, task: str | None = None) -> list[str]:
    return get_fallback_chain(model_name, task=task)


def get_retry_limit(model_name: str | None) -> int:
    profile = get_model_profile(model_name)
    try:
        return max(1, int(profile.get("retry_limit", 2)))
    except (TypeError, ValueError):
        return 2


def get_question_count(model_name: str | None) -> int:
    profile = get_model_profile(model_name)
    try:
        return max(1, int(profile.get("question_count", 5)))
    except (TypeError, ValueError):
        return 5


def get_call_delay_seconds(model_name: str | None) -> int:
    profile = get_model_profile(model_name)
    try:
        return max(0, int(profile.get("call_delay_seconds", 0)))
    except (TypeError, ValueError):
        return 0

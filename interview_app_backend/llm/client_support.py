import threading
import time
from collections.abc import Mapping

from interview_app_backend.utils.logging_config import get_llm_logger

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ModuleNotFoundError:
    genai = None
    GENAI_AVAILABLE = False

LOGGER = get_llm_logger()
MAX_ATTEMPTS_PER_MODEL = 3
_LLM_CALL_STATE = threading.local()

def _call_google(prompt: str, api_key: str, temperature: float | None = None) -> str:
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-generativeai library not installed")
    for attempt in range(MAX_ATTEMPTS_PER_MODEL):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            LOGGER.info("Calling Google Gemini - attempt %s", attempt + 1)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature or 0.7,
                    "max_output_tokens": 4096,
                },
            )
            text = response.text
            LOGGER.info("Success with Google Gemini")
            return text
        except Exception as exc:
            LOGGER.warning("Google API failed on attempt %s: %s", attempt + 1, exc)
            if attempt < MAX_ATTEMPTS_PER_MODEL - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise RuntimeError("Google API failed after retries")


def _looks_like_html(text: str) -> bool:
    lowered = text.lstrip().lower()
    return lowered.startswith("<!doctype html") or lowered.startswith("<html") or "<html" in lowered or "</html>" in lowered


def _is_auth_error(response: str) -> bool:
    lower = response.lower()
    auth_indicators = ["signed-out", "token-invalid", "auth", "login", "sign in"]
    return any(indicator in lower for indicator in auth_indicators)


def _extract_output_text(response: object, *, provider: str, model: str) -> str:
    if isinstance(response, str):
        text = str(response).strip()
        if _looks_like_html(text):
            if _is_auth_error(text):
                raise RuntimeError("Authentication failed - please check your API key")
            return ""
        if not text:
            LOGGER.warning("llm_empty_output", extra={"provider": provider, "model": model, "raw_output_length": len(text)})
        return text if text else ""
    if isinstance(response, Mapping):
        extracted = response.get("output_text", "")
        text = str(extracted).strip() if extracted else ""
        if _looks_like_html(text):
            if _is_auth_error(text):
                raise RuntimeError("Authentication failed - please check your API key")
            return ""
        if not text:
            LOGGER.warning("llm_empty_output", extra={"provider": provider, "model": model, "raw_output_length": len(text)})
        return text

    output_text = getattr(response, "output_text", "")
    if output_text:
        extracted = output_text
        text = str(extracted).strip() if extracted else ""
        if _looks_like_html(text):
            if _is_auth_error(text):
                raise RuntimeError("Authentication failed - please check your API key")
            return ""
        if not text:
            LOGGER.warning("llm_empty_output", extra={"provider": provider, "model": model, "raw_output_length": len(text)})
        return text
    LOGGER.warning("llm_empty_output", extra={"provider": provider, "model": model, "raw_output_length": len(str(output_text or ""))})
    return ""


def _extract_provider(model: str) -> str:
    if model.startswith("gemini-"):
        return "google"
    if model.startswith("grok-"):
        return "grok"
    return model.split("/")[0] if "/" in model else "unknown"


def _normalise_task_name(task: str | None) -> str:
    cleaned = str(task or "").strip()
    return cleaned or "general"


def _set_last_llm_call_metadata(*, status: str, task: str, provider: str, model: str, attempt: int | None = None) -> None:
    _LLM_CALL_STATE.last_call = {
        "status": status,
        "task": task,
        "provider": provider,
        "model": model,
        "attempt": attempt,
    }


def get_last_llm_call_metadata() -> dict[str, str | int | None]:
    metadata = getattr(_LLM_CALL_STATE, "last_call", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def clear_last_llm_call_metadata() -> None:
    if hasattr(_LLM_CALL_STATE, "last_call"):
        delattr(_LLM_CALL_STATE, "last_call")


def _log_llm_event(
    level: int,
    *,
    task: str,
    provider: str,
    model: str,
    status: str,
    attempt: int | None = None,
    detail: str | None = None,
) -> None:
    extra = {
        "task": task,
        "provider": provider,
        "model": model,
        "status": status,
    }
    if attempt is not None:
        extra["attempt"] = attempt
    if detail:
        extra["detail"] = detail

    message = f"LLM_{status.upper()} task={task} model={model}"
    if attempt is not None:
        message += f" attempt={attempt}"
    if detail:
        message += f" detail={detail}"

    LOGGER.log(level, message, extra=extra)


def _is_model_unavailable_error(exc: Exception) -> bool:
    error_str = str(exc).lower()
    return "404" in error_str or "no endpoints available" in error_str or "guardrail" in error_str


def _is_transient_error(exc: Exception) -> bool:
    status_code = _status_code_from_exception(exc)
    if status_code is not None:
        return status_code == 429 or 500 <= status_code < 600
    error_str = str(exc).lower()
    network_keywords = ["timeout", "timed out", "connection", "network", "refused", "reset", "dns"]
    return any(keyword in error_str for keyword in network_keywords)


def _is_permanent_error(exc: Exception) -> bool:
    status_code = _status_code_from_exception(exc)
    return status_code in {400, 401, 402, 403}


def _task_requires_json(task_name: str) -> bool:
    return task_name.startswith("evaluation.evidence_extraction") or task_name.startswith("evaluation.scoring")


def _status_code_from_exception(exc: Exception) -> int | None:
    for attribute in ("status_code", "status", "code"):
        value = getattr(exc, attribute, None)
        try:
            code = int(value)
        except (TypeError, ValueError):
            continue
        if code > 0:
            return code
    message = str(exc)
    for token in ("400", "401", "402", "403", "404", "429"):
        if token in message:
            return int(token)
    return None

import logging
import time
import threading
from collections.abc import Callable
from collections.abc import Mapping

try:
    from openai import OpenAI, APIError, APITimeoutError, RateLimitError
except ModuleNotFoundError:
    class OpenAI:
        pass

    class APIError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    class RateLimitError(Exception):
        pass

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ModuleNotFoundError:
    genai = None
    GENAI_AVAILABLE = False

from config.settings import APP_TITLE
from config.settings import MODEL_NAME
from config.settings import OPENROUTER_API_KEY
from config.settings import GOOGLE_API_KEY
from config.settings import LLM_TIMEOUT
from config.model_profiles import get_fallback_chain
from config.model_profiles import is_free_model
from interview_app_backend.utils.logging_config import get_llm_logger

LOGGER = get_llm_logger()
MAX_MODELS_PER_PROVIDER = 4
MAX_ATTEMPTS_PER_MODEL = 3
MAX_TOTAL_CALL_SECONDS = 12
RETRY_BACKOFF_BASE_SECONDS = 2
_LLM_CALL_STATE = threading.local()

def create_openrouter_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-OpenRouter-Title": APP_TITLE,
        },
    )

def get_openrouter_client() -> OpenAI:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")
    return create_openrouter_client(OPENROUTER_API_KEY)

def create_google_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta",
    )

def get_google_client() -> OpenAI:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set")
    return create_google_client(GOOGLE_API_KEY)


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
    network_keywords = ["timeout", "connection", "network", "refused", "reset", "dns"]
    return any(keyword in error_str for keyword in network_keywords)


def _is_permanent_error(exc: Exception) -> bool:
    status_code = _status_code_from_exception(exc)
    return status_code in {400, 402, 403}


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
    for token in ("400", "402", "403", "404", "429"):
        if token in message:
            return int(token)
    return None


PROVIDER_MODELS = {
    "open-router": MODEL_NAME,
    "grok": "grok-2-1212",
    "google": "gemini-2.0-flash",
}


def call_llm(
    prompt: str,
    client: OpenAI,
    temperature: float | None = None,
    task: str | None = None,
    provider: str | None = None,
    should_abort: Callable[[], bool] | None = None,
    max_models_per_provider: int = MAX_MODELS_PER_PROVIDER,
) -> str:
    last_error: Exception | None = None
    task_name = _normalise_task_name(task)
    primary_model = PROVIDER_MODELS.get(provider, MODEL_NAME) if provider else MODEL_NAME
    if is_free_model(primary_model):
        models_to_try = get_fallback_chain(primary_model, task=task_name)
    else:
        models_to_try = [primary_model]
    models_to_try = models_to_try[:max(1, int(max_models_per_provider))]
    call_started_at = time.monotonic()
    for model_index, model in enumerate(models_to_try):
        if should_abort and should_abort():
            raise RuntimeError("cancelled")
        provider = _extract_provider(model)
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            elapsed_seconds = time.monotonic() - call_started_at
            if elapsed_seconds >= MAX_TOTAL_CALL_SECONDS:
                break
            try:
                request_kwargs = {"model": model, "input": prompt, "timeout": LLM_TIMEOUT}
                if temperature is not None:
                    request_kwargs["temperature"] = temperature
                LOGGER.info(
                    "LLM_REQUEST",
                    extra={
                        "task": task_name,
                        "provider": provider,
                        "model": model,
                        "attempt": attempt,
                    }
                )
                response = client.responses.create(**request_kwargs)
                output_text = _extract_output_text(response, provider=provider, model=model)
                if _task_requires_json(task_name):
                    try:
                        from interview_app_backend.llm.parser import parse_json_response

                        parse_json_response(output_text, model=model, provider=provider, task=task_name)
                    except Exception as exc:
                        last_error = exc
                        reason = "invalid_schema" if exc.__class__.__name__ == "ValidationError" else "invalid_json"
                        _set_last_llm_call_metadata(status="validation_failed", task=task_name, provider=provider, model=model, attempt=attempt)
                        LOGGER.warning(
                            "LLM_VALIDATION_FAILED",
                            extra={
                                "task": task_name,
                                "provider": provider,
                                "model": model,
                                "attempt": attempt,
                                "reason": reason,
                            }
                        )
                        break
                _set_last_llm_call_metadata(status="success", task=task_name, provider=provider, model=model, attempt=attempt)
                latency_ms = int((time.monotonic() - call_started_at) * 1000)
                LOGGER.info(
                    "LLM_SUCCESS",
                    extra={
                        "task": task_name,
                        "provider": provider,
                        "model": model,
                        "latency_ms": latency_ms,
                    }
                )
                return output_text
            except (APITimeoutError, RateLimitError, APIError, RuntimeError, Exception) as exc:
                last_error = exc
                elapsed_seconds = time.monotonic() - call_started_at

                error_str = str(exc).lower()
                if "rate limit" in error_str or "429" in error_str:
                    LOGGER.warning(
                        "LLM_RATE_LIMIT",
                        extra={
                            "task": task_name,
                            "provider": provider,
                            "model": model,
                            "attempt": attempt,
                        }
                    )
                else:
                    LOGGER.debug(
                        "LLM_FAILURE",
                        extra={
                            "task": task_name,
                            "provider": provider,
                            "model": model,
                            "attempt": attempt,
                            "error": str(exc),
                        }
                    )

                if _is_permanent_error(exc):
                    _set_last_llm_call_metadata(status="failure", task=task_name, provider=provider, model=model, attempt=attempt)
                    raise RuntimeError(str(exc) or "We encountered an issue. Please try again in a few moments.") from exc
                if _is_model_unavailable_error(exc):
                    _set_last_llm_call_metadata(status="unavailable", task=task_name, provider=provider, model=model, attempt=attempt)
                    LOGGER.info(
                        "LLM_MODEL_UNAVAILABLE",
                        extra={
                            "task": task_name,
                            "provider": provider,
                            "model": model,
                            "attempt": attempt,
                        }
                    )
                    break
                if _is_transient_error(exc) and attempt < MAX_ATTEMPTS_PER_MODEL and elapsed_seconds < MAX_TOTAL_CALL_SECONDS:
                    _set_last_llm_call_metadata(status="retrying", task=task_name, provider=provider, model=model, attempt=attempt)
                    sleep_seconds = min(RETRY_BACKOFF_BASE_SECONDS ** attempt, max(0.0, MAX_TOTAL_CALL_SECONDS - elapsed_seconds))
                    if sleep_seconds > 0:
                        LOGGER.debug(
                            "LLM_RETRY",
                            extra={
                                "task": task_name,
                                "provider": provider,
                                "model": model,
                                "attempt": attempt,
                                "sleep_seconds": sleep_seconds,
                            }
                        )
                        time.sleep(sleep_seconds)
                    continue
                _set_last_llm_call_metadata(status="failure", task=task_name, provider=provider, model=model, attempt=attempt)
                break
        if model_index < len(models_to_try) - 1:
            next_model = models_to_try[model_index + 1]
            LOGGER.info(
                "LLM_FALLBACK",
                extra={
                    "task": task_name,
                    "provider": _extract_provider(next_model),
                    "model": next_model,
                }
            )
    _set_last_llm_call_metadata(status="failure", task=task_name, provider=_extract_provider(models_to_try[-1]), model=models_to_try[-1])
    LOGGER.warning(
        "LLM_FAILURE_FINAL",
        extra={
            "task": task_name,
            "model": models_to_try[-1],
            "reason": "all_retries_failed",
        }
    )
    raise RuntimeError("We encountered an issue. Please try again in a few moments.") from last_error

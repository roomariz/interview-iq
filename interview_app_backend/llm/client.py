from interview_app_backend.llm.deadline import check, remaining, pause, provider_call, DeadlineExceeded
import time
from collections.abc import Callable

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

from config.settings import APP_TITLE
from config.settings import OPENROUTER_MODEL_NAME as MODEL_NAME
from config.settings import OPENROUTER_API_KEY
from config.settings import LLM_TIMEOUT
from config.model_profiles import get_fallback_chain
from config.model_profiles import is_free_model
from interview_app_backend.utils.logging_config import get_llm_logger

from interview_app_backend.llm.client_support import (
    _extract_output_text, _extract_provider, _normalise_task_name,
    _set_last_llm_call_metadata, _is_model_unavailable_error, _is_transient_error,
    _is_permanent_error, _task_requires_json,
    get_last_llm_call_metadata, clear_last_llm_call_metadata,  # noqa: F401
)
from config import settings
from interview_app_backend.llm.ollama_client import OllamaCloudClient
from interview_app_backend.llm.google_chat import call_google_chat
from interview_app_backend.llm.provider_clients import get_grok_client, get_google_client, create_google_client  # noqa: F401

LOGGER = get_llm_logger()
MAX_MODELS_PER_PROVIDER = 4
MAX_ATTEMPTS_PER_MODEL = 3
MAX_TOTAL_CALL_SECONDS = 12
RETRY_BACKOFF_BASE_SECONDS = 2

def create_openrouter_client(api_key: str) -> OpenAI:
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-OpenRouter-Title": APP_TITLE,
        },
    )
    client.max_retries = 0
    return client

def get_openrouter_client() -> OpenAI | OllamaCloudClient:
    """Legacy service factory; honours the configured LLM provider."""
    if settings.LLM_PROVIDER == "ollama":
        return OllamaCloudClient()
    if settings.LLM_PROVIDER == "grok":
        return get_grok_client()
    if settings.LLM_PROVIDER == "google":
        return get_google_client()
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")
    return create_openrouter_client(OPENROUTER_API_KEY)

PROVIDER_MODELS = {
    "open-router": MODEL_NAME,
    "grok": settings.GROK_MODEL,
    "google": settings.GOOGLE_MODEL,
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
    check()
    if settings.LLM_PROVIDER in {"grok", "google"}:
        provider = settings.LLM_PROVIDER
    if isinstance(client, OllamaCloudClient) or provider == "ollama":
        ollama_client = client if isinstance(client, OllamaCloudClient) else OllamaCloudClient()
        try:
            output = ollama_client.call(prompt, temperature, task, should_abort)
            _set_last_llm_call_metadata(status="success", task=_normalise_task_name(task),
                                        provider="ollama", model=ollama_client.model)
            check()
            return output
        except DeadlineExceeded:
            raise
        except RuntimeError as exc:
            _set_last_llm_call_metadata(status="failure", task=_normalise_task_name(task),
                                        provider="ollama", model=ollama_client.model)
            if str(exc) == "cancelled" or not settings.OLLAMA_FALLBACK_TO_OPENROUTER:
                raise
            if not OPENROUTER_API_KEY:
                raise RuntimeError("OpenRouter fallback requires OPENROUTER_API_KEY") from exc
            client = create_openrouter_client(OPENROUTER_API_KEY)
            provider = "open-router"
    last_error: Exception | None = None
    task_name = _normalise_task_name(task)
    primary_model = PROVIDER_MODELS.get(provider, MODEL_NAME) if provider else MODEL_NAME
    use_google_chat = provider == "google"
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
            check()
            elapsed_seconds = time.monotonic() - call_started_at
            if elapsed_seconds >= MAX_TOTAL_CALL_SECONDS:
                break
            try:
                request_kwargs = {"model": model, "input": prompt, "timeout": remaining(LLM_TIMEOUT)}
                if provider == "grok":
                    request_kwargs["store"] = False
                if temperature is not None:
                    request_kwargs["temperature"] = temperature
                LOGGER.info("LLM_REQUEST", extra={"task": task_name, "provider": provider,
                                                  "model": model, "attempt": attempt})
                response = provider_call(
                    lambda request=request_kwargs: call_google_chat(client, request, task_name) if use_google_chat else client.responses.create(**request),
                    request_kwargs["timeout"],
                )
                output_text = _extract_output_text(response, provider=provider, model=model)
                if _task_requires_json(task_name):
                    try:
                        from interview_app_backend.llm.parser import parse_evidence_response, parse_json_response

                        if task_name.startswith("evaluation.evidence_extraction"):
                            parse_evidence_response(output_text)
                        else:
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
            except DeadlineExceeded:
                raise
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
                            "error": type(exc).__name__,
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
                        pause(sleep_seconds)
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
    LOGGER.warning("LLM_FAILURE_FINAL", extra={"task": task_name, "model": models_to_try[-1],
                                               "reason": "all_retries_failed"})
    raise RuntimeError("We encountered an issue. Please try again in a few moments.") from last_error

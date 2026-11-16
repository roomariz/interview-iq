from interview_app_backend.llm.deadline import check, DeadlineExceeded
import time
from dataclasses import dataclass
from typing import Any, Callable

from interview_app_backend.llm.client import call_llm as _call_openrouter
from interview_app_backend.llm.client import get_openrouter_client
from interview_app_backend.llm.provider_clients import get_google_client, get_grok_client
from interview_app_backend.utils.logging_config import get_llm_logger
from config.settings import (
    IS_FREE_MODE,  # noqa: F401
    QUESTION_GENERATION_PROVIDERS,  # noqa: F401
    QUESTION_GENERATION_FALLBACKS,  # noqa: F401
)


LOGGER = get_llm_logger()


@dataclass
class ProviderConfig:
    name: str
    client_getter: Callable[[], Any]
    api_key_getter: Callable[[], str]
    blocked: bool = False


PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "open-router": ProviderConfig(
        name="open-router",
        client_getter=get_openrouter_client,
        api_key_getter=lambda: __import__("config.settings", fromlist=["OPENROUTER_API_KEY"]).OPENROUTER_API_KEY,
    ),
    "grok": ProviderConfig(
        name="grok",
        client_getter=get_grok_client,
        api_key_getter=lambda: __import__("config.settings", fromlist=["XAI_API_KEY"]).XAI_API_KEY,
    ),
    "google": ProviderConfig(
        name="google",
        client_getter=get_google_client,
        api_key_getter=lambda: __import__("config.settings", fromlist=["GOOGLE_API_KEY"]).GOOGLE_API_KEY,
    ),
}


@dataclass
class CallLog:
    provider_used: str
    fallback_reason: str | None
    attempts: int
    response_valid: bool
    latency_ms: float
    error: str | None = None


def _call_provider(
    client: Any,
    prompt: str,
    temperature: float | None,
    task: str | None,
    provider: str,
    should_abort: Callable[[], bool] | None = None,
    max_models_per_provider: int = 1,
) -> tuple[str | None, CallLog]:
    if should_abort and should_abort():
        return None, CallLog(
            provider_used=provider,
            fallback_reason="cancelled",
            attempts=0,
            response_valid=False,
            latency_ms=0,
            error="cancelled",
        )
    start_time = time.time()
    attempts = 1

    try:
        response = _call_openrouter(
            prompt,
            client,
            temperature=temperature,
            task=task,
            provider=provider,
            should_abort=should_abort,
            max_models_per_provider=max_models_per_provider,
        )
        is_valid, validated_response, repaired = _validate_json_response(response, provider=provider)
        latency_ms = (time.time() - start_time) * 1000
        if repaired:
            LOGGER.info(
                "JSON_REPAIRED",
                extra={
                    "provider": provider,
                    "reason": "malformed_json",
                }
            )
        return validated_response, CallLog(
            provider_used=provider,
            fallback_reason=None,
            attempts=attempts,
            response_valid=is_valid,
            latency_ms=latency_ms,
            error=None if is_valid else "invalid_json",
        )
    except DeadlineExceeded:
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_str = str(e).lower()
        if "rate limit" in error_str or "429" in error_str:
            LOGGER.warning(
                "PROVIDER_RATE_LIMIT",
                extra={
                    "provider": provider,
                }
            )
        else:
            LOGGER.warning(
                "PROVIDER_FAILED",
                extra={
                    "provider": provider,
                    "error": type(e).__name__,
                }
            )
        return None, CallLog(
            provider_used=provider,
            fallback_reason=str(e),
            attempts=attempts,
            response_valid=False,
            latency_ms=latency_ms,
            error=str(e),
        )


def _call_provider_with_retry(
    client_getter: Callable[[], Any],
    prompt: str,
    temperature: float | None,
    task: str | None,
    provider: str,
    max_retries: int = 1,
    should_abort: Callable[[], bool] | None = None,
    max_models_per_provider: int = 1,
) -> tuple[str | None, CallLog]:
    last_log: CallLog | None = None
    response = None

    for attempt in range(max_retries + 1):
        check()
        if should_abort and should_abort():
            return None, CallLog(
                provider_used=provider,
                fallback_reason="cancelled",
                attempts=attempt,
                response_valid=False,
                latency_ms=0,
                error="cancelled",
            )
        try:
            client = client_getter()
            response, last_log = _call_provider(
                client,
                prompt,
                temperature,
                task,
                provider,
                should_abort=should_abort,
                max_models_per_provider=max_models_per_provider,
            )
            if response and last_log.response_valid:
                return response, last_log
            if attempt < max_retries:
                LOGGER.debug(
                    "PROVIDER_RETRY",
                    extra={
                        "provider": provider,
                        "attempt": attempt + 2,
                    }
                )
                last_log = CallLog(
                    provider_used=provider,
                    fallback_reason="invalid_json_retry",
                    attempts=attempt + 2,
                    response_valid=False,
                    latency_ms=last_log.latency_ms if last_log else 0,
                    error="retry_after_invalid",
                )
        except DeadlineExceeded:
            raise
        except Exception as e:
            LOGGER.warning(
                "PROVIDER_ATTEMPT_FAILED",
                extra={
                    "provider": provider,
                    "attempt": attempt + 1,
                    "error": type(e).__name__,
                }
            )
            last_log = CallLog(
                provider_used=provider,
                fallback_reason=str(e),
                attempts=attempt + 1,
                response_valid=False,
                latency_ms=0,
                error=str(e),
            )
            break

    return response, last_log


from interview_app_backend.llm.fallback_validation import _validate_json_response, _is_network_error  # noqa: E402, F401

from interview_app_backend.llm.fallback_dispatch import call_with_fallback, call_llm_with_fallback  # noqa: E402, F401

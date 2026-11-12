import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from interview_app_backend.llm.client import call_llm as _call_openrouter
from interview_app_backend.llm.client import get_openrouter_client
from interview_app_backend.llm.json_utils import repair_json_payload
from interview_app_backend.llm.provider_clients import get_google_client, get_grok_client
from interview_app_backend.utils.logging_config import get_llm_logger
from config.settings import (
    ALLOWED_PROVIDERS,
    IS_FREE_MODE,
    QUESTION_GENERATION_PROVIDERS,
    QUESTION_GENERATION_FALLBACKS,
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
                    "error": str(e),
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
        except Exception as e:
            LOGGER.warning(
                "PROVIDER_ATTEMPT_FAILED",
                extra={
                    "provider": provider,
                    "attempt": attempt + 1,
                    "error": str(e),
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


def _validate_json_response(response: str, provider: str) -> tuple[bool, str, bool]:
    if not response or not response.strip():
        return False, response, False
    try:
        json.loads(response.strip())
        return True, response.strip(), False
    except (json.JSONDecodeError, ValueError, TypeError):
        repaired = repair_json_payload(response)
        if repaired:
            return True, repaired, True
        LOGGER.warning(
            "JSON_VALIDATION_FAILED",
            extra={
                "provider": provider,
                "reason": "invalid_json",
            }
        )
        return False, response, False


def _is_network_error(error: Exception) -> bool:
    error_str = str(error).lower()
    network_keywords = ["timeout", "connection", "network", "refused", "reset", "dns"]
    return any(keyword in error_str for keyword in network_keywords)


def call_with_fallback(
    prompt: str,
    primary_providers: list[str],
    fallback_providers: list[str],
    temperature: float | None = None,
    task: str | None = None,
    max_retries_per_provider: int = 1,
    require_valid_json: bool = True,
    should_abort: Callable[[], bool] | None = None,
    max_models_per_provider: int = 1,
) -> tuple[str | None, CallLog]:
    all_providers = primary_providers + ([] if IS_FREE_MODE else fallback_providers)

    if should_abort and should_abort():
        return None, CallLog(
            provider_used="cancelled",
            fallback_reason="cancelled",
            attempts=0,
            response_valid=False,
            latency_ms=0,
            error="cancelled",
        )

    for provider_key in all_providers:
        if should_abort and should_abort():
            return None, CallLog(
                provider_used=provider_key,
                fallback_reason="cancelled",
                attempts=0,
                response_valid=False,
                latency_ms=0,
                error="cancelled",
            )
        config = PROVIDER_CONFIGS.get(provider_key)
        if not config:
            LOGGER.warning(
                "UNKNOWN_PROVIDER",
                extra={"provider": provider_key}
            )
            continue

        if config.api_key_getter is None:
            LOGGER.warning(
                "PROVIDER_NO_API_KEY",
                extra={"provider": provider_key}
            )
            continue

        api_key = config.api_key_getter()
        if not api_key:
            LOGGER.warning(
                "PROVIDER_EMPTY_API_KEY",
                extra={"provider": provider_key}
            )
            continue

        response, call_log = _call_provider_with_retry(
            config.client_getter,
            prompt,
            temperature,
            task,
            provider_key,
            max_retries=max_retries_per_provider,
            should_abort=should_abort,
            max_models_per_provider=max_models_per_provider,
        )

        LOGGER.info(
            "PROVIDER_CALL_COMPLETE",
            extra={
                "provider": provider_key,
                "valid": call_log.response_valid,
                "fallback_reason": call_log.fallback_reason,
                "attempts": call_log.attempts,
                "latency_ms": call_log.latency_ms,
            }
        )

        if response and call_log.response_valid:
            if provider_key in fallback_providers:
                call_log.fallback_reason = f"primary_failed"
            return response, call_log

        if provider_key == all_providers[-1] or (require_valid_json and not call_log.response_valid):
            continue

    return None, CallLog(
        provider_used="none",
        fallback_reason="all_providers_failed",
        attempts=0,
        response_valid=False,
        latency_ms=0,
        error="no_provider_succeeded",
    )


def call_llm_with_fallback(
    prompt: str,
    temperature: float | None = None,
    task: str | None = None,
    for_question_generation: bool = True,
    max_retries_per_provider: int = 1,
    should_abort: Callable[[], bool] | None = None,
    max_models_per_provider: int = 1,
) -> tuple[str | None, CallLog]:
    if for_question_generation:
        return call_with_fallback(
            prompt=prompt,
            primary_providers=QUESTION_GENERATION_PROVIDERS,
            fallback_providers=QUESTION_GENERATION_FALLBACKS,
            temperature=temperature,
            task=task,
            max_retries_per_provider=max_retries_per_provider,
            require_valid_json=True,
            should_abort=should_abort,
            max_models_per_provider=max_models_per_provider,
        )

    return call_with_fallback(
        prompt=prompt,
        primary_providers=QUESTION_GENERATION_PROVIDERS,
        fallback_providers=QUESTION_GENERATION_FALLBACKS,
        temperature=temperature,
        task=task,
        max_retries_per_provider=max_retries_per_provider,
        require_valid_json=True,
        should_abort=should_abort,
        max_models_per_provider=max_models_per_provider,
    )

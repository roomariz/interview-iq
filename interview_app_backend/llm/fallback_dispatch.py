"""Provider dispatch using the existing compatibility module state."""

from typing import Callable
from interview_app_backend.llm import provider_fallback as service

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
) -> tuple[str | None, service.CallLog]:
    all_providers = primary_providers + ([] if service.IS_FREE_MODE else fallback_providers)

    if should_abort and should_abort():
        return None, service.CallLog(
            provider_used="cancelled",
            fallback_reason="cancelled",
            attempts=0,
            response_valid=False,
            latency_ms=0,
            error="cancelled",
        )

    for provider_key in all_providers:
        service.check()
        if should_abort and should_abort():
            return None, service.CallLog(
                provider_used=provider_key,
                fallback_reason="cancelled",
                attempts=0,
                response_valid=False,
                latency_ms=0,
                error="cancelled",
            )
        config = service.PROVIDER_CONFIGS.get(provider_key)
        if not config:
            service.LOGGER.warning(
                "UNKNOWN_PROVIDER",
                extra={"provider": provider_key}
            )
            continue

        if config.api_key_getter is None:
            service.LOGGER.warning(
                "PROVIDER_NO_API_KEY",
                extra={"provider": provider_key}
            )
            continue

        api_key = config.api_key_getter()
        if not api_key:
            service.LOGGER.warning(
                "PROVIDER_EMPTY_API_KEY",
                extra={"provider": provider_key}
            )
            continue

        response, call_log = service._call_provider_with_retry(
            config.client_getter,
            prompt,
            temperature,
            task,
            provider_key,
            max_retries=max_retries_per_provider,
            should_abort=should_abort,
            max_models_per_provider=max_models_per_provider,
        )

        service.LOGGER.info(
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
                call_log.fallback_reason = "primary_failed"
            return response, call_log

        if provider_key == all_providers[-1] or (require_valid_json and not call_log.response_valid):
            continue

    return None, service.CallLog(
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
) -> tuple[str | None, service.CallLog]:
    if for_question_generation:
        return call_with_fallback(
            prompt=prompt,
            primary_providers=service.QUESTION_GENERATION_PROVIDERS,
            fallback_providers=service.QUESTION_GENERATION_FALLBACKS,
            temperature=temperature,
            task=task,
            max_retries_per_provider=max_retries_per_provider,
            require_valid_json=True,
            should_abort=should_abort,
            max_models_per_provider=max_models_per_provider,
        )

    return call_with_fallback(
        prompt=prompt,
        primary_providers=service.QUESTION_GENERATION_PROVIDERS,
        fallback_providers=service.QUESTION_GENERATION_FALLBACKS,
        temperature=temperature,
        task=task,
        max_retries_per_provider=max_retries_per_provider,
        require_valid_json=True,
        should_abort=should_abort,
        max_models_per_provider=max_models_per_provider,
    )

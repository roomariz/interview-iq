"""Ollama's documented cloud HTTP API, without a local Ollama dependency."""

import json
import time
from collections.abc import Callable

import requests
from pydantic import ValidationError

from config import settings
from config.model_profiles import get_model_profile
from interview_app_backend.llm.question_generation_parser import parse_question_generation_response
from interview_app_backend.utils.logging_config import get_llm_logger

LOGGER = get_llm_logger()
MAX_ATTEMPTS = 2


def _validate_output(text: str, task: str, prompt: str = "") -> None:
    from interview_app_backend.llm.parser import parse_evidence_response, parse_json_response

    if not text.strip():
        raise ValueError("empty_response")
    if task.startswith("evaluation.evidence_extraction"):
        parse_evidence_response(text)
    elif task.startswith("evaluation.scoring"):
        parse_json_response(text, provider="ollama", task=task)
    elif task.startswith("question_generation."):
        from interview_app_backend.llm.question_contract import request_contract, validate_question_response

        # Match the prompt profile used by the existing question service.
        strict = bool(get_model_profile(settings.MODEL_NAME)["strict_json"])
        json.loads(text)
        if strict:
            contract = request_contract(prompt)
            validate_question_response(text, contract["count"], contract["distribution"])
        elif not parse_question_generation_response(text, strict=False):
            raise ValueError("invalid_question_schema")


class OllamaCloudClient:
    def __init__(self) -> None:
        self.model = {"gemma4:cloud": "gemma4:31b"}.get(settings.OLLAMA_MODEL, settings.OLLAMA_MODEL)

    def call(
        self,
        prompt: str,
        temperature: float | None,
        task: str | None,
        should_abort: Callable[[], bool] | None = None,
    ) -> str:
        if should_abort and should_abort():
            raise RuntimeError("cancelled")
        if settings.OLLAMA_HOST.rstrip("/") != "https://ollama.com":
            raise RuntimeError("OLLAMA_HOST must be https://ollama.com for Ollama Cloud")
        if not settings.OLLAMA_API_KEY:
            raise RuntimeError("OLLAMA_API_KEY is not set")
        if not self.model or settings.LLM_TIMEOUT <= 0:
            raise RuntimeError("Configure a non-empty OLLAMA_MODEL and positive LLM_TIMEOUT")
        if not isinstance(prompt, str) or not prompt.strip() or "\x00" in prompt:
            raise RuntimeError("Invalid LLM prompt")

        task_name = task or "general"
        structured = task_name.startswith(("question_generation.", "evaluation.evidence_extraction", "evaluation.scoring"))
        messages = []
        if structured:
            messages.append({"role": "system", "content": "Return only valid JSON matching the schema in the request. No Markdown."})
        messages.append({"role": "user", "content": prompt})
        body = {"model": self.model, "messages": messages, "stream": False}
        if temperature is not None:
            body["options"] = {"temperature": temperature}
        # Cloud does not support `format`/schema-constrained output.
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if should_abort and should_abort():
                raise RuntimeError("cancelled")
            failure = "invalid_response"
            retryable = True
            validation_error = None
            try:
                response = requests.post(
                    "https://ollama.com/api/chat",
                    headers={"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"},
                    json=body,
                    timeout=settings.LLM_TIMEOUT,
                    allow_redirects=False,
                )
                if response.status_code != 200:
                    status = response.status_code
                    failure = {401: "authentication_failed", 403: "authentication_failed", 429: "rate_limited"}.get(status, f"http_{status}")
                    retryable = status == 429 or 500 <= status < 600
                else:
                    payload = response.json()
                    if not isinstance(payload, dict) or payload.get("error") or payload.get("done") is not True:
                        raise ValueError("incomplete_response")
                    message = payload.get("message")
                    text = message.get("content") if isinstance(message, dict) else None
                    if not isinstance(text, str):
                        raise ValueError("invalid_response")
                    _validate_output(text, task_name, prompt)
                    LOGGER.info("LLM_SUCCESS", extra={"provider": "ollama", "model": self.model, "task": task_name, "attempt": attempt})
                    return text.strip()
            except requests.Timeout:
                failure = "timeout"
            except requests.RequestException:
                failure = "connection_failed"
            except (ValueError, TypeError, ValidationError) as exc:
                failure = "invalid_json_or_schema"
                validation_error = exc
            LOGGER.warning("OLLAMA_FAILURE", extra={"reason": failure, "attempt": attempt, "task": task_name})
            if not retryable or attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Ollama Cloud request failed ({failure}). Please check configuration or try again.") from validation_error
            time.sleep(2 ** (attempt - 1))
        raise RuntimeError("Ollama Cloud request failed")  # pragma: no cover

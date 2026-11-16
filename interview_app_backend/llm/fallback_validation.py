"""Existing provider response validation helpers."""

import json
from interview_app_backend.llm.json_utils import repair_json_payload
from interview_app_backend.utils.logging_config import get_llm_logger

LOGGER = get_llm_logger()

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

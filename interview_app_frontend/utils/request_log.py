import time
import streamlit as st
from typing import Any


def _get_reason_from_log(log: dict[str, Any]) -> str:
    error = log.get("error", "")
    fallback = log.get("fallback_reason", "")
    status = log.get("status", "")

    if status in ("pending", "running"):
        return "in_progress"
    if status == "rate_limited":
        return "quota_exhausted"
    if error:
        error_lower = str(error).lower()
        if "rate limit" in error_lower or "429" in error_lower:
            if "quota" in error_lower or "daily" in error_lower:
                return "quota_exhausted"
            return "temporary_rate_limit"
        if "json" in error_lower:
            return "validation_failed"
        return "invalid_response"
    if fallback:
        fallback_lower = str(fallback).lower()
        if "primary" in fallback_lower:
            return "primary_failed"
        if "cancelled" in fallback_lower:
            return "cancelled"
    return fallback or "unknown"


def _get_status_from_log(log: dict[str, Any]) -> str:
    error = log.get("error", "")
    fallback = log.get("fallback_reason", "")
    status = log.get("status", "")
    success = log.get("success", True)

    if status in ("pending", "running"):
        return "WARNING"
    if status in ("failed", "timeout") or error or not success:
        return "FAIL"
    if fallback and "primary" in str(fallback).lower():
        return "SWITCH"
    if log.get("attempts", 1) > 1:
        return "WARNING"
    return "OK"


def log_request(
    task: str,
    provider: str = "unknown",
    model: str = "",
    status: str = "pending",
    error: str = "",
    fallback_reason: str | None = None,
    attempts: int = 1,
    latency_ms: float = 0,
) -> None:
    if "request_log" not in st.session_state:
        st.session_state.request_log = []

    model_display = model if model else provider

    log_entry = {
        "timestamp": time.time(),
        "task": task,
        "provider": provider,
        "model": model_display,
        "attempts": attempts,
        "fallback_reason": fallback_reason,
        "status": status,
        "error": error,
        "latency_ms": latency_ms,
        "success": status == "completed",
    }

    st.session_state.request_log.append(log_entry)


def get_log_summary() -> list[dict[str, Any]]:
    logs = st.session_state.get("request_log", [])
    summary = []

    for log in logs:
        status = _get_status_from_log(log)
        reason = _get_reason_from_log(log)
        is_fallback = bool(log.get("fallback_reason") and "primary" in str(log.get("fallback_reason")).lower())

        model = log.get("model", log.get("provider", "unknown"))

        summary.append({
            "time": time.strftime("%H:%M:%S", time.localtime(log["timestamp"])),
            "task": log["task"],
            "primary_model": model,
            "attempts": log.get("attempts", 1),
            "Fall back": "Yes" if is_fallback else "No",
            "Final Status": status,
            "Reason": reason,
            "Latency": f"{log.get('latency_ms', 0)/1000:.1f}s" if log.get("latency_ms") else "—",
            "details": _build_details(log),
        })

    return summary


def _build_details(log: dict[str, Any]) -> list[str]:
    details = []
    provider = log.get("provider", "unknown")
    model = log.get("model", provider)
    attempts = log.get("attempts", 1)
    error = log.get("error", "")
    fallback = log.get("fallback_reason", "")
    status = log.get("status", "")
    success = log.get("success", True)

    display_model = model if model != provider else provider

    for i in range(1, attempts + 1):
        details.append(f"Attempt {i} → {display_model} → {'OK' if success else 'FAIL'}")

    if fallback:
        details.append(f"Fallback → {fallback}")

    final_status = "OK" if success else "FAILED"
    details.append(f"Final → {final_status}")

    if error:
        details.append(f"Error: {error}")
    elif status == "rate_limited":
        details.append("Reason: Rate limit reached")

    return details


def clear_request_log() -> None:
    st.session_state.request_log = []


def has_request_logs() -> bool:
    return bool(st.session_state.get("request_log", []))


def update_pending_request(
    task: str,
    status: str,
    error: str = "",
    provider: str = "",
    model: str = "",
    attempts: int = 1,
    latency_ms: float = 0,
    fallback_reason: str | None = None,
) -> None:
    logs = st.session_state.get("request_log", [])
    for log in reversed(logs):
        if log.get("task") == task and log.get("status") == "pending":
            log["status"] = status
            log["error"] = error
            if provider:
                log["provider"] = provider
            if model:
                log["model"] = model
            log["attempts"] = attempts
            log["latency_ms"] = latency_ms
            log["fallback_reason"] = fallback_reason
            log["success"] = status == "completed"
            break


def get_status_counts() -> dict[str, int]:
    logs = st.session_state.get("request_log", [])
    counts = {"OK": 0, "WARNING": 0, "FAIL": 0, "SWITCH": 0}

    for log in logs:
        status = _get_status_from_log(log)
        if status in counts:
            counts[status] += 1

    return counts

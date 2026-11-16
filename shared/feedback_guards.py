"""Pure output guards used by service and display layers."""

def example_text(value):
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text in {"{}", "[]", "null"} or text.startswith(("{", "[", "```")):
        return ""
    return text


def memory_is_allowed(data):
    trust = data.get("trust", {})
    warning = data.get("validation_warning", {})
    feedback = data.get("feedback", data)
    return bool(
        data.get("memory_storage_allowed", False)
        and data.get("feedback_validation", {}).get("status") == "checked"
        and data.get("topic_match", True) and not data.get("relevance_gate_applied", False)
        and trust.get("trust_level") in {"medium", "high"}
        and float(trust.get("score_confidence", 0) or 0) >= 0.4
        and warning.get("severity") != "high"
        and any(feedback.get(key) for key in ("strengths", "key_issues", "improvements"))
    )

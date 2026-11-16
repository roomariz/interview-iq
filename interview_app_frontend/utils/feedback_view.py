from collections.abc import Mapping
from typing import Any

from interview_app_frontend.utils.feedback_model import FEEDBACK_DIMENSIONS


def _text_items(view_model: Mapping[str, Any]) -> str:
    pieces = []
    for key in ("key_issues", "improvements"):
        pieces.extend(str(item).lower() for item in view_model.get(key, []) if str(item).strip())
    pieces.extend(str(item).lower() for item in view_model.get("strengths", []) if str(item).strip())
    return " ".join(pieces)


def build_score_consistency(view_model: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for key, label in FEEDBACK_DIMENSIONS:
        score = int(view_model["scores"].get(key, 0))
        text = str(view_model["labels"].get(key, "")).strip().lower()
        if score <= 3 and any(token in text for token in ("strong", "excellent")):
            issues.append(label)
        if score >= 8 and any(token in text for token in ("weak", "needs improvement", "lacks")):
            issues.append(label)
    if int(view_model["scores"].get("relevance", 0)) > 5 and not bool(view_model.get("topic_match", True)):
        issues.append("Relevance score inconsistent with answer content")
    base_decision = str(view_model["overall_decision_detail"].get("score_based_value") or view_model["overall_decision"]).strip()
    visible_decision = str(view_model["overall_decision"]).strip()
    return {
        "issues": issues,
        "base_decision": base_decision,
        "visible_decision": visible_decision,
        "has_gap": bool(issues or base_decision != visible_decision),
        "note": (
            "Score consistency check: visible decision and score-based verdict differ. "
            "This is a trust cue, not a user-facing error."
        )
        if base_decision != visible_decision
        else "",
    }


def build_key_takeaway(view_model: Mapping[str, Any]) -> str:
    if str(view_model.get("failure_type", "")).strip() == "off_topic" or not bool(view_model.get("topic_match", True)):
        return "Key takeaway: The answer does not address the question."
    if not view_model.get("memory_storage_allowed", False):
        return "Key takeaway: Evaluation is provisional; no established weakness recorded."
    strengths = [str(item).strip() for item in view_model.get("strengths", []) if str(item).strip()]
    improvements = prioritise_improvements(view_model)
    issues = [str(item).strip() for item in view_model.get("key_issues", []) if str(item).strip()]
    if strengths and improvements:
        return f"Key takeaway: {strengths[0]}. Next step: {improvements[0]}"
    if strengths:
        return f"Key takeaway: {strengths[0]}."
    if improvements:
        return f"Key takeaway: Next step: {improvements[0]}"
    if issues:
        return f"Key takeaway: Focus on {issues[0].lower()}."
    return "Key takeaway: Keep the answer concrete, structured, and decision-led."


def prioritise_improvements(view_model: Mapping[str, Any]) -> list[str]:
    improvements = [str(item).strip() for item in view_model.get("improvements", []) if str(item).strip()]
    if len(improvements) < 2:
        return improvements
    issue_text = _text_items(view_model)
    ranked = []
    for index, improvement in enumerate(improvements):
        lowered = improvement.lower()
        score = 0
        if any(token in lowered for token in ("metric", "measure", "impact")) and "metric" in issue_text:
            score += 4
        if any(token in lowered for token in ("trade-off", "alternative")) and any(token in issue_text for token in ("trade-off", "alternative")):
            score += 4
        if any(token in lowered for token in ("structure", "star")) and any(token in issue_text for token in ("structure", "star")):
            score += 4
        if any(token in lowered for token in ("ownership", "contribution")) and any(token in issue_text for token in ("ownership", "impact")):
            score += 4
        score += max(0, 3 - index)
        ranked.append((-score, index, improvement))
    ranked.sort()
    return [item[2] for item in ranked]


def prioritise_strengths(view_model: Mapping[str, Any]) -> list[str]:
    strengths = [str(item).strip() for item in view_model.get("strengths", []) if str(item).strip()]
    if len(strengths) < 2:
        return strengths
    keywords = {
        "relevance": ("direct", "relevant", "focused", "aligned"),
        "structure": ("structure", "clear", "flow", "star"),
        "specificity": ("metric", "measure", "quant", "impact", "result"),
        "communication": ("communication", "explain", "concise", "easy to follow"),
        "problem_solving_approach": ("reason", "trade-off", "alternative", "decision", "approach"),
    }
    ranked = []
    for index, strength in enumerate(strengths):
        lowered = strength.lower()
        matches = [int(view_model["scores"].get(key, 0)) for key, tokens in keywords.items() if any(token in lowered for token in tokens)]
        match_score = max(matches) if matches else 0
        match_score += min(len(matches), 3) * 0.2
        match_score -= sum(2 for token in ("weak", "lacks", "missing") if token in lowered)
        ranked.append((-match_score, index, strength))
    ranked.sort()
    return [item[2] for item in ranked]


def build_follow_up(view_model: Mapping[str, Any]) -> dict[str, str]:
    from interview_app_backend.services.question_followup import question_bound_followup

    follow_up = dict(view_model.get("follow_up", {}))
    if follow_up.get("context_note", "").startswith("Original question:"):
        return follow_up
    return question_bound_followup(
        str(view_model.get("question", "")), str(view_model.get("answer", "")),
        {"status": "off_topic" if view_model.get("failure_type") == "off_topic" else "relevant"},
    )


def build_behaviour_aware_trust(view_model: Mapping[str, Any]) -> dict[str, str]:
    trust = dict(view_model.get("trust", {}))
    validation = dict(view_model.get("validation_warning", {}))
    consistency = build_score_consistency(view_model)
    severity = str(validation.get("severity", "info")).strip()
    trust_level = str(trust.get("trust_level", "unknown")).strip()
    decision_confidence = str(trust.get("decision_confidence", "unknown")).strip()
    summary = f"{trust_level.capitalize()} confidence in the feedback. Decision confidence: {decision_confidence}."
    if severity in {"high", "medium"}:
        summary = f"{summary} Read the scores as provisional."
    if consistency["has_gap"]:
        summary = f"{summary} The visible verdict is softened by the score pattern."
    detail = str(trust.get("trust_definition", "")).strip() or str(validation.get("interpretation", "")).strip()
    if not detail:
        detail = str(view_model.get("overall_decision_detail", {}).get("reason", "")).strip()
    return {
        "summary": summary,
        "detail": detail,
        "decision": f"Decision confidence: {decision_confidence.capitalize()}",
        "depth": f"Evaluation depth: {validation.get('reasoning_depth', 'unknown').replace('_', ' ').capitalize()}",
    }

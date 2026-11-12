from collections.abc import Mapping
from typing import Any

from interview_app_frontend.utils.feedback_model import FEEDBACK_DIMENSIONS


def _text_items(view_model: Mapping[str, Any]) -> str:
    pieces = []
    for key in ("key_issues", "improvements"):
        pieces.extend(str(item).lower() for item in view_model.get(key, []) if str(item).strip())
    pieces.extend(str(item).lower() for item in view_model.get("strengths", []) if str(item).strip())
    return " ".join(pieces)


def _reasoning_action(depth: str) -> str:
    return {
        "none": "State why you chose this answer and name one concrete decision.",
        "implicit": "Explain why this approach was better than a simpler alternative.",
        "developing": "Add one rejected option and one trade-off you accepted.",
        "explicit": "Connect the decision to constraints, evidence, and the result.",
        "deep": "Summarise the trade-off and the impact in one crisp closing sentence.",
    }.get(depth, "Turn the reasoning into one explicit decision and one trade-off.")


def _follow_up_is_grounded(follow_up: Mapping[str, Any], issue_text: str, improvement_text: str, scores: Mapping[str, Any]) -> bool:
    question = str(follow_up.get("question", "")).lower()
    target_dimension = str(follow_up.get("target_dimension", "")).strip()
    if not question:
        return False
    if target_dimension == "relevance":
        return "system performance" in question or "measurable" in question
    if target_dimension == "specificity":
        if "trade-off" in issue_text or "alternative" in issue_text:
            return False
        return any(token in question for token in ("metric", "impact", "measure")) and any(token in issue_text for token in ("metric", "impact", "measure"))
    if target_dimension == "problem_solving_approach":
        if int(scores.get("specificity", 0)) <= 4:
            return False
        return any(token in question for token in ("trade-off", "alternative", "tradeoff", "quantify", "metric", "measure"))
    if target_dimension == "structure":
        return any(token in question for token in ("structure", "situation", "task", "action", "result", "star"))
    if "trade-off" in issue_text or "alternative" in issue_text:
        if int(scores.get("specificity", 0)) <= 4:
            return True
        return any(token in question for token in ("trade-off", "alternative", "tradeoff"))
    if "metric" in issue_text or "impact" in issue_text or "metric" in improvement_text or "impact" in improvement_text:
        return any(token in question for token in ("metric", "impact", "measure", "quantify"))
    return True


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
    follow_up = dict(view_model.get("follow_up", {}))
    memory = list(view_model.get("future_session_memory", [])) if isinstance(view_model.get("future_session_memory"), list) else []
    stage = min(len(memory) + 1, 3)
    failure_type = str(view_model.get("failure_type", "")).strip()
    relevance_score = int(view_model.get("scores", {}).get("relevance", 0))
    issue_text = " ".join(str(item).lower() for item in view_model.get("key_issues", []) if str(item).strip())
    improvement_text = " ".join(str(item).lower() for item in view_model.get("improvements", []) if str(item).strip())
    if failure_type == "off_topic" or relevance_score < 3 or not bool(view_model.get("topic_match", True)):
        follow_up["question"] = "Can you describe a real example where you improved system performance under constraints with measurable results?"
        follow_up["type"] = "relevance_gate"
        follow_up["target_dimension"] = "relevance"
        follow_up["reasoning_action"] = "Answer the question directly with one concrete example and the result."
        follow_up["context_note"] = "Grounded in the original system-performance question."
        follow_up["stage"] = stage
        return follow_up
    if follow_up.get("question") and _follow_up_is_grounded(follow_up, issue_text, improvement_text, view_model.get("scores", {})):
        if not follow_up.get("reasoning_action"):
            follow_up["reasoning_action"] = _reasoning_action(str(view_model["validation_warning"].get("reasoning_depth", "implicit")))
        follow_up["stage"] = stage
        return follow_up
    weakest_key, weakest_label = min(FEEDBACK_DIMENSIONS, key=lambda item: int(view_model["scores"].get(item[0], 0)))
    depth = str(view_model["validation_warning"].get("reasoning_depth", "implicit"))
    if stage >= 3 and memory:
        question = "How would you summarise the main lesson from this answer for your next interview?"
        target_dimension = weakest_key
        context = "future session memory"
    elif stage >= 2 and memory:
        question = "What would you do differently the next time you face the same gap?"
        target_dimension = weakest_key
        context = "repeat gap"
    elif "metric" in issue_text or "impact" in issue_text:
        question = "How would you prove the impact of this change with one concrete metric?"
        target_dimension = "specificity"
        context = "metrics and impact"
    elif (("trade-off" in issue_text or "alternative" in issue_text) and int(view_model["scores"].get("specificity", 0)) > 4):
        question = "What alternative did you reject, and what trade-off made this choice better?"
        target_dimension = "problem_solving_approach"
        context = "trade-offs and alternatives"
    elif "structure" in issue_text or "star" in issue_text:
        question = "How would you reshape this answer into a clearer Situation-Task-Action-Result flow?"
        target_dimension = "structure"
        context = "structure and flow"
    elif "ownership" in issue_text or "impact" in issue_text:
        question = "What was your specific contribution, and what changed because of it?"
        target_dimension = "relevance"
        context = "ownership and impact"
    else:
        context = weakest_label.lower()
        question = (
            "How would you explain why this was the right trade-off compared with one alternative?"
            if weakest_key == "problem_solving_approach"
            else f"What would you change if you had to strengthen the {context} part of this answer?"
        )
        target_dimension = weakest_key
    return {
        "question": question,
        "type": "depth_probe",
        "target_dimension": target_dimension,
        "reasoning_action": _reasoning_action(depth),
        "context_note": f"Grounded in {context}.",
        "stage": stage,
    }


def build_behaviour_aware_trust(view_model: Mapping[str, Any]) -> dict[str, str]:
    trust = dict(view_model.get("trust", {}))
    validation = dict(view_model.get("validation_warning", {}))
    consistency = build_score_consistency(view_model)
    severity = str(validation.get("severity", "info")).strip()
    trust_level = str(trust.get("trust_level", "unknown")).strip()
    decision_confidence = str(trust.get("decision_confidence", "unknown")).strip()
    score_confidence = float(trust.get("score_confidence", 0.0) or 0.0)
    summary = f"Moderate confidence in both the feedback and the decision." if trust_level == "medium" else f"{trust_level.capitalize()} confidence in both the feedback and the decision."
    if severity in {"high", "medium"}:
        summary = f"{summary} Read the scores as provisional."
    if consistency["has_gap"]:
        summary = f"{summary} The visible verdict is softened by the score pattern."
    detail = str(trust.get("trust_definition", "")).strip() or str(validation.get("interpretation", "")).strip()
    if not detail:
        detail = str(view_model.get("overall_decision_detail", {}).get("reason", "")).strip()
    if str(view_model.get("failure_type", "")).strip() == "low_specificity":
        detail = "The answer addresses the question, but it lacks measurable results and deeper reasoning."
    return {
        "summary": summary,
        "detail": detail,
        "decision": f"Decision confidence: {decision_confidence.capitalize()}",
        "depth": f"Evaluation depth: {validation.get('reasoning_depth', 'unknown').replace('_', ' ').capitalize()}",
    }

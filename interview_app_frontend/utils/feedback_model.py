from interview_app_backend.services.feedback_integrity import example_text, memory_is_allowed
from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.trust_defaults import build_fallback_review_state


FEEDBACK_DIMENSIONS = (
    ("relevance", "Relevance"),
    ("structure", "Structure"),
    ("specificity", "Specificity"),
    ("communication", "Communication"),
    ("problem_solving_approach", "Problem-Solving Approach"),
)

DEFAULT_FEEDBACK = {
    "question": "", "answer": "", "overall_decision": "fail",
    "scores": dict.fromkeys((key for key, _ in FEEDBACK_DIMENSIONS), 0),
    "labels": dict.fromkeys((key for key, _ in FEEDBACK_DIMENSIONS), ""),
    "key_issues": [], "improvements": [], "strengths": [], "criteria": [],
    "reasoning": dict.fromkeys(("clarity", "alternative_approaches", "trade_off_awareness", "evidence"), ""),
    "follow_up": {"question": "", "type": "", "target_dimension": ""},
    "example_answer": "",
}


def _clamp_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(10, score))


def score_band(score: Any) -> str:
    value = _clamp_score(score)
    if value <= 3:
        return "Weak"
    if value <= 6:
        return "Needs improvement"
    if value <= 8:
        return "Strong"
    return "Excellent"


def score_bar(score: Any, width: int = 10) -> str:
    value = _clamp_score(score)
    width = max(1, width)
    filled = min(width, round(value / 10 * width))
    return f"{'█' * filled}{'░' * (width - filled)}"


def _extract_source(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, list) and raw and isinstance(raw[-1], Mapping):
        return dict(raw[-1])
    return {}


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _coerce_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _merge_list(source: Any, fallback: list[str]) -> list[str]:
    if isinstance(source, list):
        values = [str(item).strip() for item in source if str(item).strip()]
        return values
    if isinstance(source, str) and source.strip():
        return [source.strip()]
    return fallback


def has_structured_feedback(raw: Any) -> bool:
    if isinstance(raw, Mapping):
        return True
    if isinstance(raw, list):
        return any(isinstance(item, Mapping) for item in raw)
    return False


def _derive_overall_decision(scores: Mapping[str, Any]) -> str:
    values = [_clamp_score(scores.get(key)) for key, _ in FEEDBACK_DIMENSIONS]
    if not any(values):
        return DEFAULT_FEEDBACK["overall_decision"]
    average = sum(values) / len(values)
    reasoning_score = _clamp_score(scores.get("problem_solving_approach"))
    if average >= 7 and reasoning_score >= 6:
        return "pass"
    if average < 5 or reasoning_score <= 4:
        return "fail"
    return "borderline pass"


def normalise_feedback_payload(raw: Any) -> dict[str, Any]:
    source = _extract_source(raw)
    evaluation_source = _coerce_mapping(source.get("evaluation"))
    feedback_source = _coerce_mapping(source.get("feedback"))
    reasoning_source = source.get("reasoning")
    if not isinstance(reasoning_source, Mapping):
        reasoning_source = source.get("reasoning_feedback")
    if not isinstance(reasoning_source, Mapping):
        reasoning_source = source.get("reasoning_assessment")
    reasoning = dict(reasoning_source) if isinstance(reasoning_source, Mapping) else DEFAULT_FEEDBACK["reasoning"]
    follow_up = _coerce_mapping(source.get("follow_up"))
    decision_detail = _coerce_mapping(source.get("overall_decision_detail"))
    validation_warning = _coerce_mapping(source.get("validation_warning"))
    trust_source = _coerce_mapping(source.get("trust")) or _coerce_mapping(validation_warning.get("trust")) or decision_detail

    scores = _coerce_mapping(source.get("scores"))
    labels = _coerce_mapping(source.get("labels"))
    if not scores and isinstance(evaluation_source.get("scores"), Mapping):
        scores = dict(evaluation_source["scores"])
    if not labels and isinstance(evaluation_source.get("labels"), Mapping):
        labels = dict(evaluation_source["labels"])
    topic_match = bool(source.get("topic_match", evaluation_source.get("topic_match", True)))
    relevance_gate_applied = bool(source.get("relevance_gate_applied", evaluation_source.get("relevance_gate_applied", False)))
    fallback_state = build_fallback_review_state(scores, topic_match=topic_match, relevance_gate_applied=relevance_gate_applied, overall_decision=str(source.get("overall_decision", evaluation_source.get("overall_decision", ""))).strip())

    overall_decision = str(
        source.get("overall_decision", evaluation_source.get("overall_decision", source.get("decision", "")))
    ).strip().lower()
    if overall_decision not in {"pass", "borderline pass", "fail"}:
        overall_decision = _derive_overall_decision(scores)

    feedback_summary = str(feedback_source.get("summary", source.get("summary", source.get("overall_summary", "")))).strip()
    if not feedback_summary:
        feedback_summary = DEFAULT_FEEDBACK["reasoning"]["clarity"]
    trust = {
        key: (trust_source.get(key) if not _is_blank(trust_source.get(key)) else fallback_state["trust"][key])
        for key in fallback_state["trust"]
    }
    validation_warning_source = validation_warning
    validation_warning = {
        key: (validation_warning_source.get(key) if not _is_blank(validation_warning_source.get(key)) else fallback_state["validation_warning"][key])
        for key in fallback_state["validation_warning"]
    }
    decision_detail_source = decision_detail
    decision_detail = {
        key: (decision_detail_source.get(key) if not _is_blank(decision_detail_source.get(key)) else fallback_state["overall_decision_detail"][key])
        for key in fallback_state["overall_decision_detail"]
    }
    failure_type = str(source.get("failure_type", evaluation_source.get("failure_type", fallback_state["failure_type"]))).strip() or fallback_state["failure_type"]

    return {
        "question": str(source.get("question", DEFAULT_FEEDBACK["question"])).strip(),
        "answer": str(source.get("answer", DEFAULT_FEEDBACK["answer"])).strip(),
        "assessment_status": source.get("assessment_status", "provisional"),
        "overall_decision": overall_decision,
        "scores": {
            key: _clamp_score(source.get(key, scores.get(key, DEFAULT_FEEDBACK["scores"][key])))
            for key, _ in FEEDBACK_DIMENSIONS
        },
        "labels": {
            key: str(source.get(key, labels.get(key, DEFAULT_FEEDBACK["labels"][key]))).strip()
            for key, _ in FEEDBACK_DIMENSIONS
        },
        "summary": feedback_summary,
        "key_issues": _merge_list(feedback_source.get("key_issues", source.get("key_issues", source.get("weak_points"))), DEFAULT_FEEDBACK["key_issues"]),
        "improvements": _merge_list(feedback_source.get("improvements", source.get("improvements", source.get("improvement_areas"))), DEFAULT_FEEDBACK["improvements"]),
        "strengths": _merge_list(feedback_source.get("strengths", source.get("strengths")), DEFAULT_FEEDBACK["strengths"]),
        "criteria": _merge_list(source.get("criteria"), DEFAULT_FEEDBACK["criteria"]),
        "reasoning": {
            "clarity": str(reasoning.get("clarity", DEFAULT_FEEDBACK["reasoning"]["clarity"])).strip(),
            "alternative_approaches": str(reasoning.get("alternative_approaches", DEFAULT_FEEDBACK["reasoning"]["alternative_approaches"])).strip(),
            "trade_off_awareness": str(reasoning.get("trade_off_awareness", DEFAULT_FEEDBACK["reasoning"]["trade_off_awareness"])).strip(),
            "evidence": str(reasoning.get("evidence", DEFAULT_FEEDBACK["reasoning"]["evidence"])).strip(),
        },
        "follow_up": {
            "question": str(follow_up.get("question", DEFAULT_FEEDBACK["follow_up"]["question"])).strip(),
            "type": str(follow_up.get("type", DEFAULT_FEEDBACK["follow_up"]["type"])).strip(),
            "target_dimension": str(follow_up.get("target_dimension", "")).strip(),
            **{key: follow_up[key] for key in ("reasoning_action", "context_note", "stage") if key in follow_up},
        },
        "topic_match": bool(source.get("topic_match", evaluation_source.get("topic_match", True))),
        "relevance_gate_applied": bool(source.get("relevance_gate_applied", evaluation_source.get("relevance_gate_applied", False))),
        "failure_type": failure_type,
        "memory_storage_allowed": memory_is_allowed(source),
        "feedback_validation": source.get("feedback_validation", {}),
        "future_session_memory": list(source.get("future_session_memory", [])) if isinstance(source.get("future_session_memory"), list) else [],
        "overall_decision_detail": {key: (str(value).strip() if isinstance(value, str) else _coerce_float(value) if key == "score_confidence" else bool(value) if key == "gating_applied" else value) for key, value in decision_detail.items()},
        "validation_warning": {key: (str(value).strip() if isinstance(value, str) else _coerce_float(value) if key == "score_confidence" else bool(value) if key == "has_warning" else value) for key, value in validation_warning.items()},
        "trust": {key: (str(value).strip() if key != "score_confidence" else _coerce_float(value)) for key, value in trust.items()},
        "example_answer": example_text(source.get("example_answer")),
    }

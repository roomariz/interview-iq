"""Existing deterministic score rules, shared with display normalisation."""
from collections.abc import Mapping
from typing import Any

def derive_overall_decision(scores: Mapping[str, Any]) -> str:
    values = [int(scores.get(key) or 0) for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")]
    if not any(values):
        return "fail"
    average = sum(values) / len(values)
    reasoning_score = values[4]
    if average >= 7 and reasoning_score >= 6:
        return "pass"
    if average < 5 or reasoning_score <= 4:
        return "fail"
    return "borderline pass"


def classify_fallback_failure(scores: Mapping[str, Any], topic_match: bool, relevance_gate_applied: bool) -> str:
    if relevance_gate_applied or not topic_match:
        return "off_topic"
    relevance = int(scores.get("relevance") or 0)
    specificity = int(scores.get("specificity") or 0)
    reasoning = int(scores.get("problem_solving_approach") or 0)
    if relevance >= 4 and specificity <= 4 and reasoning <= 5:
        return "low_specificity"
    if relevance >= 4 and specificity >= 5 and reasoning <= 5:
        return "low_evidence"
    if relevance >= 4 and reasoning <= 5:
        return "low_evidence"
    return "none"

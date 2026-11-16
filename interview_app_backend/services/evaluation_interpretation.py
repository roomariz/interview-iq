from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_signals import (
    ANOMALY_PENALTIES,
    CONTRADICTION_PENALTIES,
    GENERIC_ALTERNATIVE_PHRASES,
    GENERIC_METRIC_PHRASES,
    GENERIC_REASONING_PHRASES,
    GENERIC_STRUCTURE_PHRASES,
    GENERIC_TRADEOFF_PHRASES,
    REASONING_DEPTH_DEFINITIONS,
    SEVERITY_DEFINITIONS,
    TRUST_LEVEL_DEFINITIONS,
    classify_reasoning_depth,
    _clamp,
    _has_phrase,
    _unique,
)


def _normalise_items(items: list[str], phrases: set[str], replacement: str, flag: str) -> tuple[list[str], list[str]]:
    cleaned: list[str] = []
    hits: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if _has_phrase(text, phrases):
            cleaned.append(replacement)
            hits.append(flag)
            continue
        cleaned.append(text)
    return cleaned, hits


def build_dimension_contradictions(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> dict[str, list[str]]:
    labels = dict(evaluation.get("labels", {})) if isinstance(evaluation.get("labels"), Mapping) else {}
    feedback = dict(evaluation.get("feedback", {})) if isinstance(evaluation.get("feedback"), Mapping) else {}
    reasoning = dict(evaluation.get("reasoning", {})) if isinstance(evaluation.get("reasoning"), Mapping) else {}
    key_issues = [str(item).lower() for item in feedback.get("key_issues", [])] if isinstance(feedback.get("key_issues"), list) else []
    improvements = [str(item).lower() for item in feedback.get("improvements", [])] if isinstance(feedback.get("improvements"), list) else []
    buckets = {"metrics": [], "structure": [], "reasoning": [], "tradeoffs": [], "alternatives": []}
    if evaluation_context.get("has_metrics") and any(_has_phrase(str(item), GENERIC_METRIC_PHRASES) for item in [labels.get("specificity", ""), *key_issues, *improvements]):
        buckets["metrics"].append("metrics_contradiction")
    if evaluation_context.get("has_structure") and any(_has_phrase(str(item), GENERIC_STRUCTURE_PHRASES) for item in [labels.get("structure", ""), *key_issues, *improvements]):
        buckets["structure"].append("structure_contradiction")
    if evaluation_context.get("has_reasoning") and any(_has_phrase(str(item), GENERIC_REASONING_PHRASES) for item in [reasoning.get("evidence", ""), reasoning.get("clarity", ""), *key_issues, *improvements]):
        buckets["reasoning"].append("reasoning_contradiction")
    if evaluation_context.get("has_tradeoffs") and any(_has_phrase(str(item), GENERIC_TRADEOFF_PHRASES) for item in [reasoning.get("trade_off_awareness", ""), *key_issues, *improvements]):
        buckets["tradeoffs"].append("tradeoff_contradiction")
    if evaluation_context.get("has_alternatives") and any(_has_phrase(str(item), GENERIC_ALTERNATIVE_PHRASES) for item in [reasoning.get("alternative_approaches", ""), *key_issues, *improvements]):
        buckets["alternatives"].append("alternatives_contradiction")
    return {key: _unique(value) for key, value in buckets.items() if value}


def _score_confidence(evaluation_context: Mapping[str, Any], dimension_contradictions: Mapping[str, list[str]]) -> float:
    confidence = dict(evaluation_context.get("confidence", {}))
    if evaluation_context.get("question_type", "behavioural") != "behavioural":
        confidence.pop("metrics", None)
    base = sum(confidence.values()) / max(len(confidence), 1)
    penalty = sum(CONTRADICTION_PENALTIES.get(flag, 0.08) for flags in dimension_contradictions.values() for flag in flags)
    penalty += sum(ANOMALY_PENALTIES.get(flag, 0.06) for flag in evaluation_context.get("anomaly_flags", []))
    return _clamp(base - penalty)


def _trust_level(score_confidence: float, severity: str, impact_strength: str) -> str:
    if severity == "high" or score_confidence < 0.45:
        return "low"
    if severity == "medium" or score_confidence < 0.78:
        return "medium"
    return "high"


def _interpretation(trust_level: str, reasoning_depth: str, impact_strength: str) -> str:
    if trust_level == "low":
        return "Treat the scores as provisional; the flags affect interpretation."
    if trust_level == "medium":
        return f"Use with caution; {reasoning_depth} reasoning and {impact_strength} impact strength affect interpretation."
    return f"Use normally; {reasoning_depth} reasoning and {impact_strength} impact strength are aligned."


def _anomaly_influence(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any], dimension_contradictions: Mapping[str, list[str]], reasoning_depth: str) -> dict[str, Any]:
    anomaly_flags = _unique(list(evaluation_context.get("anomaly_flags", [])) + [flag for flags in dimension_contradictions.values() for flag in flags if flag in ANOMALY_PENALTIES])
    contradiction_flags = _unique(list(evaluation_context.get("contradiction_flags", [])) + [flag for flags in dimension_contradictions.values() for flag in flags])
    reasons: list[str] = []
    affected_dimensions: list[str] = []
    affects_score_confidence = False
    affects_trust_level = bool(contradiction_flags)
    if contradiction_flags:
        reasons.append("Contradiction flags reduce trust level.")
    if "misleading_metrics" in anomaly_flags:
        affects_score_confidence = True
        affected_dimensions.append("specificity")
        reasons.append("Misleading metrics weaken specificity confidence.")
    if "ambiguous_metrics" in anomaly_flags:
        affects_score_confidence = True
        affected_dimensions.append("specificity")
        reasons.append("Ambiguous metrics reduce specificity confidence.")
    if any(flag in anomaly_flags for flag in {"fake_metrics", "non_impact_numbers"}):
        affects_score_confidence = True
        affected_dimensions.append("specificity")
        reasons.append("Fake or non-impact numbers do not increase specificity confidence.")
    if "classifier_conflict" in anomaly_flags:
        affects_score_confidence = True
        affects_trust_level = True
        affected_dimensions.append("relevance")
        reasons.append("Classifier conflict weakens relevance confidence.")
    if reasoning_depth in {"none", "implicit"}:
        affects_score_confidence = True
        affected_dimensions.append("problem_solving_approach")
        reasons.append("Thin reasoning reduces problem-solving confidence.")
    if any(flag in dimension_contradictions for flag in {"reasoning", "tradeoffs", "alternatives"}):
        affects_score_confidence = True
        affected_dimensions.append("problem_solving_approach")
        reasons.append("Reasoning-related contradictions reduce problem-solving confidence.")
    if not reasons:
        return {"affects_score_confidence": False, "affects_trust_level": False, "affected_dimensions": [], "impact": "none", "reasons": []}
    impact = "major" if affects_trust_level and (len(reasons) >= 2 or "misleading_metrics" in anomaly_flags) else "moderate" if affects_score_confidence and affects_trust_level else "minor"
    return {
        "affects_score_confidence": affects_score_confidence,
        "affects_trust_level": affects_trust_level,
        "affected_dimensions": _unique(affected_dimensions),
        "impact": impact,
        "reasons": reasons,
    }


def build_validation_warning(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any], dimension_contradictions: Mapping[str, list[str]]) -> dict[str, Any]:
    reasoning_depth = classify_reasoning_depth(evaluation, evaluation_context)
    impact_strength = str(evaluation_context.get("impact_strength", "weak"))
    anomaly_influence = _anomaly_influence(evaluation, evaluation_context, dimension_contradictions, reasoning_depth)
    anomaly_flags = _unique(list(evaluation_context.get("anomaly_flags", [])) + [flag for flags in dimension_contradictions.values() for flag in flags if flag in ANOMALY_PENALTIES])
    contradiction_flags = _unique(list(evaluation_context.get("contradiction_flags", [])) + [flag for flags in dimension_contradictions.values() for flag in flags])
    severity = "high" if any(flag.endswith("contradiction") for flag in contradiction_flags) or "misleading_metrics" in anomaly_flags else "medium" if anomaly_flags else "low" if contradiction_flags else "info"
    score_confidence = _score_confidence({**evaluation_context, "reasoning_depth": reasoning_depth, "anomaly_flags": anomaly_flags}, dimension_contradictions)
    trust_level = _trust_level(score_confidence, severity, impact_strength if evaluation_context.get("question_type", "behavioural") == "behavioural" else "not_applicable")
    validation_block = {
        "severity": severity,
        "severity_definition": SEVERITY_DEFINITIONS[severity],
        "trust_level": trust_level,
        "trust_definition": TRUST_LEVEL_DEFINITIONS[trust_level],
        "score_confidence": score_confidence,
        "impact_strength": impact_strength,
        "contradiction_flags": contradiction_flags,
        "anomaly_flags": anomaly_flags,
        "anomaly_influence": anomaly_influence,
        "grouped_anomaly_flags": {
            "numeric": _unique([flag for flag in anomaly_flags if flag in {"ambiguous_metrics", "fake_metrics"}]),
            "directional": ["misleading_metrics"] if "misleading_metrics" in anomaly_flags else [],
            "non_impact": ["non_impact_numbers"] if "non_impact_numbers" in anomaly_flags else [],
        },
    }
    trust_block = {
        "trust_level": trust_level,
        "trust_definition": TRUST_LEVEL_DEFINITIONS[trust_level],
        "score_confidence": score_confidence,
        "impact_strength": impact_strength,
        "anomaly_influence": anomaly_influence,
    }
    reasoning_block = {
        "reasoning_depth": reasoning_depth,
        "reasoning_depth_definition": REASONING_DEPTH_DEFINITIONS[reasoning_depth],
    }
    return {
        "has_warning": bool(contradiction_flags or anomaly_flags),
        "severity": severity,
        "severity_definition": SEVERITY_DEFINITIONS[severity],
        "trust_level": trust_level,
        "trust_definition": TRUST_LEVEL_DEFINITIONS[trust_level],
        "reasoning_depth": reasoning_depth,
        "reasoning_depth_definition": REASONING_DEPTH_DEFINITIONS[reasoning_depth],
        "score_confidence": score_confidence,
        "interpretation": _interpretation(trust_level, reasoning_depth, impact_strength),
        "contradiction_flags": contradiction_flags,
        "dimension_contradictions": {key: value for key, value in dimension_contradictions.items() if value},
        "anomaly_flags": anomaly_flags,
        "validation": validation_block,
        "reasoning": reasoning_block,
        "grouped_anomaly_flags": validation_block["grouped_anomaly_flags"],
    }


def apply_evaluation_consistency(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(evaluation)
    labels = dict(data.get("labels", {}))
    feedback = dict(data.get("feedback", {}))
    scores = dict(data.get("scores", {}))
    warnings: list[str] = []
    relevance_score = int(scores.get("relevance") or 0)
    topic_match = bool(evaluation_context.get("topic_match", True))
    if relevance_score > 5 and not topic_match:
        warnings.append("Relevance score contradicts the answer content and was normalised.")
        scores["relevance"] = min(relevance_score, 3)
    metrics_detected = bool(evaluation_context.get("metrics_detected") or evaluation_context.get("has_metrics") or evaluation_context.get("metric_count"))
    if metrics_detected:
        cleaned, hits = _normalise_items([str(labels.get("specificity", ""))], GENERIC_METRIC_PHRASES, "Metrics are present, but could be tied more clearly to business or user impact.", "metrics_contradiction")
        labels["specificity"] = cleaned[0] if cleaned else ""
        if hits:
            warnings.append("Specificity label contradicted extracted metrics and was normalised.")
    if evaluation_context.get("question_type", "behavioural") == "behavioural" and not metrics_detected and "specificity" in scores:
        scores["specificity"] = min(int(scores.get("specificity") or 0), 3)
    if evaluation_context.get("has_structure"):
        cleaned, hits = _normalise_items([str(labels.get("structure", ""))], GENERIC_STRUCTURE_PHRASES, "Clear sections are present.", "structure_contradiction")
        labels["structure"] = cleaned[0] if cleaned else ""
        if hits:
            warnings.append("Structure label contradicted extracted structure and was normalised.")
    dimension_map = (
        ("metrics", GENERIC_METRIC_PHRASES, "The answer includes measurable evidence.", "Keep the existing metrics, but briefly connect them to user or business impact."),
        ("structure", GENERIC_STRUCTURE_PHRASES, "The answer has a structured flow.", "Keep the existing logical sequence."),
        ("reasoning", GENERIC_REASONING_PHRASES, "The answer includes reasoning.", "Add one sentence on why this approach was preferred."),
        ("tradeoffs", GENERIC_TRADEOFF_PHRASES, "The answer mentions trade-offs or constraints.", "Name the trade-off you accepted and why it was reasonable."),
        ("alternatives", GENERIC_ALTERNATIVE_PHRASES, "The answer mentions alternatives.", "Briefly compare one alternative approach."),
    )
    dimension_contradictions = build_dimension_contradictions(data, evaluation_context)
    contradiction_flags = list(evaluation_context.get("contradiction_flags", []))
    for dimension, phrases, issue_replacement, improvement_replacement in dimension_map:
        if dimension not in dimension_contradictions:
            continue
        key_issues = feedback.get("key_issues", []) if isinstance(feedback.get("key_issues"), list) else []
        cleaned, hits = _normalise_items(key_issues, phrases, issue_replacement, f"{dimension}_contradiction")
        if hits:
            warnings.append(f"Normalised {dimension} feedback against the extracted evidence.")
        feedback["key_issues"] = cleaned
        improvements = feedback.get("improvements", []) if isinstance(feedback.get("improvements"), list) else []
        cleaned, hits = _normalise_items(improvements, phrases, improvement_replacement, f"{dimension}_contradiction")
        if hits:
            warnings.append(f"Reworded {dimension} improvement to match the extracted evidence.")
        feedback["improvements"] = cleaned
        contradiction_flags.extend(dimension_contradictions[dimension])
    data["scores"] = scores
    data["labels"] = labels
    data["feedback"] = feedback
    data["reasoning_depth"] = classify_reasoning_depth(data, evaluation_context)
    data["contradiction_flags"] = _unique(contradiction_flags)
    warning = build_validation_warning(data, {**evaluation_context, "anomaly_flags": list(evaluation_context.get("anomaly_flags", []))}, dimension_contradictions)
    data["score_confidence"] = warning["score_confidence"]
    data["validation_warning"] = warning
    data["validation_warnings"] = warnings + ([warning["interpretation"]] if warning["has_warning"] else [])
    return data

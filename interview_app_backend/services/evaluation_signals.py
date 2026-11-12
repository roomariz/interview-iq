import re
from collections.abc import Mapping
from typing import Any


GENERIC_METRIC_PHRASES = {
    "missing specific metrics for improvement",
    "lacks measurable outcomes",
    "missing measurable outcomes",
    "add quantifiable results such as latency reduction or throughput gains",
}
GENERIC_STRUCTURE_PHRASES = {
    "needs clearer structure",
    "needs clearer star organisation",
    "needs clearer star organization",
    "lacks structure",
}
GENERIC_REASONING_PHRASES = {
    "needs clearer reasoning",
    "reasoning is implicit",
    "lacks reasoning",
    "why this solution is not clear",
    "explain why",
}
GENERIC_TRADEOFF_PHRASES = {
    "trade-offs are missing",
    "needs clearer trade-off discussion",
    "lacks trade-off awareness",
    "did not discuss trade-offs",
}
GENERIC_ALTERNATIVE_PHRASES = {
    "alternative approaches were not discussed",
    "no alternatives considered",
    "did not consider alternatives",
    "lacks alternative approaches",
}
STRUCTURE_MARKERS = {"challenge", "approach", "results", "result", "situation", "task", "action"}
REASONING_MARKERS = {"because", "so that", "therefore", "as a result", "which meant", "to reduce", "to improve"}
TRADEOFF_MARKERS = {"trade-off", "tradeoff", "trade-offs", "tradeoffs", "risk", "complexity", "budget"}
ALTERNATIVE_MARKERS = {"alternative", "alternatives", "instead", "considered", "rejected", "compared"}
IMPACT_MARKERS = {"improved", "reduced", "increased", "decreased", "faster", "latency", "throughput", "error", "cost", "cpu"}
HYPE_MARKERS = {"better", "massive", "huge", "dramatically", "significantly"}
NUMERIC_PATTERNS = (
    re.compile(r"-\d+(?:\.\d+)?%"),
    re.compile(r"\b\d+(?:\.\d+)?%"),
    re.compile(r"\b\d+(?:\.\d+)?x\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|sec|secs|seconds|minutes|hours|gb|mb|tb)\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\b"),
)
VERSION_PATTERN = re.compile(r"\bv?\d+(?:\.\d+){1,2}\b", re.IGNORECASE)
VERSION_TAG_PATTERN = re.compile(r"\bv\d+\b", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
EVALUATION_VERSION = "trust-v4"
CONTRADICTION_PENALTIES = {
    "metrics_contradiction": 0.12,
    "structure_contradiction": 0.1,
    "reasoning_contradiction": 0.12,
    "tradeoff_contradiction": 0.1,
    "alternatives_contradiction": 0.1,
}
ANOMALY_PENALTIES = {
    "ambiguous_metrics": 0.05,
    "fake_metrics": 0.14,
    "non_impact_numbers": 0.1,
    "misleading_metrics": 0.18,
    "classifier_conflict": 0.12,
}
SEVERITY_DEFINITIONS = {
    "info": "No material conflict; the output can be read normally.",
    "low": "Minor anomaly; the output remains usable but should be read cautiously.",
    "medium": "Mixed evidence; the output should influence interpretation, not override it.",
    "high": "Material contradiction or misleading metric; the output should be treated as low trust.",
}
TRUST_LEVEL_DEFINITIONS = {
    "high": "High confidence and low conflict; use the result directly.",
    "medium": "Moderate confidence; use the result with caution.",
    "low": "Low confidence or strong conflict; treat the result as provisional.",
}
REASONING_DEPTH_DEFINITIONS = {
    "none": "No meaningful reasoning or justification is present.",
    "implicit": "Actions are listed, but the rationale is mostly unstated.",
    "developing": "Some rationale is present, but trade-offs or alternatives are limited.",
    "explicit": "Clear rationale is linked to constraints and decisions.",
    "deep": "Rationale, constraints, trade-offs, alternatives, and impact are clearly connected.",
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(1.0, numerator / denominator), 2)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def _has_phrase(text: str, phrases: set[str]) -> bool:
    lowered = text.strip().lower()
    return lowered in phrases or any(phrase in lowered for phrase in phrases)


def _local_numeric_signals(answer: str) -> dict[str, list[str]]:
    matches: list[str] = []
    for pattern in NUMERIC_PATTERNS:
        matches.extend(match.group(0) for match in pattern.finditer(answer))
    impactful: list[str] = []
    ambiguous: list[str] = []
    non_impact: list[str] = []
    fake: list[str] = []
    misleading: list[str] = []
    lowered = answer.lower()
    for match in matches:
        start = lowered.find(match.lower())
        window = lowered[max(0, start - 30) : min(len(lowered), start + len(match) + 30)]
        if YEAR_PATTERN.fullmatch(match) or VERSION_PATTERN.fullmatch(match) or VERSION_TAG_PATTERN.search(window) or any(marker in window for marker in {"version", "release", "team of", "engineers", "people"}):
            non_impact.append(match)
            continue
        if any(marker in window for marker in IMPACT_MARKERS) or "%" in match or "ms" in match.lower() or "x" in match.lower():
            impactful.append(match)
            if match.startswith("-"):
                misleading.append(match)
            if ("%" in match or "x" in match.lower()) and (not any(marker in window for marker in {"from", "to", "before", "after", "baseline"}) or any(marker in window for marker in HYPE_MARKERS)):
                fake.append(match)
            continue
        ambiguous.append(match)
    return {
        "detected": _unique(matches),
        "impactful": _unique(impactful),
        "ambiguous": _unique(ambiguous),
        "non_impact": _unique(non_impact),
        "fake": _unique(fake),
        "misleading": _unique(misleading),
    }


def classify_reasoning_depth(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> str:
    scores = evaluation.get("scores", {}) if isinstance(evaluation.get("scores"), Mapping) else {}
    approach = int(scores.get("problem_solving_approach") or 0)
    action_count = int(evaluation_context.get("action_count") or 0)
    markers = len(evaluation_context.get("reasoning_markers", [])) + len(evaluation_context.get("tradeoff_markers", [])) + len(evaluation_context.get("alternative_markers", []))
    has_reasoning = bool(evaluation_context.get("has_reasoning"))
    if not has_reasoning and not action_count and not markers and approach <= 1:
        return "none"
    if not has_reasoning and (action_count or approach <= 3):
        return "implicit"
    if has_reasoning and markers >= 3 and approach >= 8:
        return "deep"
    if has_reasoning and (markers >= 2 or approach >= 6 or action_count):
        return "explicit"
    return "developing"


def _impact_strength(evaluation_context: Mapping[str, Any]) -> str:
    signal_count = len(evaluation_context.get("numeric_signals", [])) + len(evaluation_context.get("fallback_numeric_signals", []))
    anomaly_count = len(evaluation_context.get("anomaly_flags", []))
    if signal_count >= 2 and anomaly_count == 0:
        return "strong"
    if signal_count >= 1:
        return "moderate"
    return "weak"


def build_evaluation_context(evidence: Mapping[str, Any], answer: str = "") -> dict[str, Any]:
    metrics = evidence.get("metrics") if isinstance(evidence.get("metrics"), list) else []
    actions = evidence.get("actions") if isinstance(evidence.get("actions"), list) else []
    local_numbers = _local_numeric_signals(answer)
    answer_text = answer.lower()
    structure_markers = sorted({marker for marker in STRUCTURE_MARKERS if marker in answer_text})
    reasoning_markers = sorted({marker for marker in REASONING_MARKERS if marker in answer_text})
    tradeoff_markers = sorted({marker for marker in TRADEOFF_MARKERS if marker in answer_text})
    alternative_markers = sorted({marker for marker in ALTERNATIVE_MARKERS if marker in answer_text})
    has_local_metrics = bool(evidence.get("has_metrics") or metrics or local_numbers["impactful"])
    contradiction_flags = _unique(
        [
            "metrics_contradiction" if local_numbers["impactful"] and not evidence.get("has_metrics") else "",
            "structure_contradiction" if structure_markers and not evidence.get("has_structure") else "",
            "reasoning_contradiction" if reasoning_markers and not evidence.get("has_reasoning") else "",
            "tradeoff_contradiction" if tradeoff_markers and not evidence.get("has_tradeoffs") else "",
            "alternatives_contradiction" if alternative_markers and not evidence.get("has_alternatives") else "",
        ]
    )
    anomaly_flags = _unique(local_numbers["ambiguous"] and ["ambiguous_metrics"] or [])
    anomaly_flags.extend(local_numbers["fake"] and ["fake_metrics"] or [])
    anomaly_flags.extend(local_numbers["non_impact"] and ["non_impact_numbers"] or [])
    anomaly_flags.extend(local_numbers["misleading"] and ["misleading_metrics"] or [])
    anomaly_flags = _unique(anomaly_flags)
    impact_strength = _impact_strength({
        "confidence": {
            "metrics": _ratio(len(metrics) + len(local_numbers["impactful"]), len(local_numbers["detected"]) + len(metrics) + 1),
        },
        "numeric_signals": local_numbers["detected"],
        "fallback_numeric_signals": local_numbers["impactful"],
    })
    reasoning_depth = classify_reasoning_depth({"scores": {}, **evidence}, {
        "has_reasoning": bool(evidence.get("has_reasoning")),
        "reasoning_markers": reasoning_markers,
        "tradeoff_markers": tradeoff_markers,
        "alternative_markers": alternative_markers,
    })
    evaluation_trace = [
        f"version:{EVALUATION_VERSION}",
        f"impact_strength:{impact_strength}",
        f"reasoning_depth:{reasoning_depth}",
        f"anomalies:{','.join(anomaly_flags) if anomaly_flags else 'none'}",
    ]
    return {
        "evaluation_version": EVALUATION_VERSION,
        "evaluation_trace": evaluation_trace,
        "has_metrics": has_local_metrics,
        "metrics_detected": has_local_metrics,
        "metric_count": len(metrics) or len(local_numbers["impactful"]),
        "has_structure": bool(evidence.get("has_structure")),
        "has_reasoning": bool(evidence.get("has_reasoning")),
        "has_tradeoffs": bool(evidence.get("has_tradeoffs")),
        "has_alternatives": bool(evidence.get("has_alternatives")),
        "confidence": {
            "metrics": _ratio(len(metrics) + len(local_numbers["impactful"]), len(local_numbers["detected"]) + len(metrics) + 1),
            "structure": 0.92 if evidence.get("has_structure") or structure_markers else 0.28,
            "reasoning": 0.92 if evidence.get("has_reasoning") or reasoning_markers else 0.28,
            "tradeoffs": 0.9 if evidence.get("has_tradeoffs") or tradeoff_markers else 0.24,
            "alternatives": 0.9 if evidence.get("has_alternatives") or alternative_markers else 0.24,
        },
        "contradiction_flags": contradiction_flags,
        "anomaly_flags": anomaly_flags,
        "grouped_anomaly_flags": {
            "numeric": _unique(local_numbers["ambiguous"] + local_numbers["fake"]),
            "directional": local_numbers["misleading"],
            "non_impact": local_numbers["non_impact"],
        },
        "numeric_signals": local_numbers["detected"],
        "fallback_numeric_signals": local_numbers["impactful"],
        "structure_markers": structure_markers,
        "reasoning_markers": reasoning_markers,
        "tradeoff_markers": tradeoff_markers,
        "alternative_markers": alternative_markers,
        "reasoning_depth": reasoning_depth,
        "impact_strength": impact_strength,
        "action_count": len(actions),
    }

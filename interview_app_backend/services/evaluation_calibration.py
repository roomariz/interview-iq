from collections.abc import Mapping
from typing import Any


NORMALISE_EVALUATION_SCORES = False

CALIBRATION_DATASET = (
    {
        "id": "excellent_metrics_reasoning",
        "description": "Excellent answer with strong metrics, structure, reasoning, trade-offs, and alternatives.",
        "expected_score_band": "excellent",
        "expected_trust_level": "high",
        "expected_reasoning_depth": "deep",
    },
    {
        "id": "good_metrics_weaker_reasoning",
        "description": "Good answer with metrics but weaker reasoning.",
        "expected_score_band": "good",
        "expected_trust_level": "medium",
        "expected_reasoning_depth": "developing",
    },
    {
        "id": "weak_vague_claims",
        "description": "Weak answer with vague claims and no metrics.",
        "expected_score_band": "weak",
        "expected_trust_level": "low",
        "expected_reasoning_depth": "none",
    },
    {
        "id": "misleading_metric_answer",
        "description": "Misleading metric answer with directionally incorrect or fake-looking metrics.",
        "expected_score_band": "borderline",
        "expected_trust_level": "low",
        "expected_reasoning_depth": "implicit",
    },
    {
        "id": "relevant_off_structure_answer",
        "description": "Off-structure but relevant answer.",
        "expected_score_band": "borderline",
        "expected_trust_level": "medium",
        "expected_reasoning_depth": "implicit",
    },
    {
        "id": "polished_shallow_answer",
        "description": "Polished but shallow answer.",
        "expected_score_band": "good",
        "expected_trust_level": "medium",
        "expected_reasoning_depth": "implicit",
    },
)

CALIBRATION_BAND_TARGETS = {"excellent": 8.8, "good": 7.2, "borderline": 5.6, "weak": 3.2}
ALLOWED_SCORE_BANDS = frozenset(CALIBRATION_BAND_TARGETS)
ALLOWED_TRUST_LEVELS = frozenset({"high", "medium", "low"})
ALLOWED_REASONING_DEPTHS = frozenset({"none", "implicit", "developing", "explicit", "deep"})


def get_calibration_dataset() -> list[dict[str, str]]:
    return [dict(item) for item in CALIBRATION_DATASET]


def validate_calibration_dataset() -> bool:
    required = {"id", "description", "expected_score_band", "expected_trust_level", "expected_reasoning_depth"}
    return all(
        required.issubset(case)
        and case["expected_score_band"] in ALLOWED_SCORE_BANDS
        and case["expected_trust_level"] in ALLOWED_TRUST_LEVELS
        and case["expected_reasoning_depth"] in ALLOWED_REASONING_DEPTHS
        for case in CALIBRATION_DATASET
    )


def confidence_level_from_value(value: float | int | None) -> str:
    if value is None:
        return "low"
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def score_band_from_average(raw_average: float) -> str:
    if raw_average >= 8.5:
        return "excellent"
    if raw_average >= 6.5:
        return "good"
    if raw_average >= 4.5:
        return "borderline"
    return "weak"


def build_normalisation_detail(scores: Mapping[str, Any], enabled: bool = NORMALISE_EVALUATION_SCORES) -> dict[str, Any]:
    values = [max(0, min(10, int(scores.get(key) or 0))) for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")]
    raw_average = round(sum(values) / len(values), 2) if values else 0.0
    band = score_band_from_average(raw_average)
    detail = {
        "enabled": enabled,
        "method": "calibration_band_v1",
        "raw_average": raw_average,
        "normalised_average": CALIBRATION_BAND_TARGETS[band] if enabled else None,
        "note": "Normalisation disabled by default" if not enabled else f"Normalised using {band} calibration band",
    }
    detail["detail"] = None if not enabled else {"band": band, "raw_average": raw_average, "normalised_average": CALIBRATION_BAND_TARGETS[band], "method": detail["method"]}
    return detail


def decision_confidence_from_trust(trust_level: str, score_confidence: str) -> str:
    if trust_level == "high":
        return score_confidence
    if trust_level == "medium":
        return "medium"
    return "low"

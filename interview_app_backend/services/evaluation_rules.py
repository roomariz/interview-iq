from shared.scoring import derive_overall_decision, classify_fallback_failure  # noqa: F401
import logging
from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_calibration import (
    build_normalisation_detail,
    confidence_level_from_value,
    decision_confidence_from_trust,
)
from interview_app_backend.services.evaluation_insights import apply_evaluation_consistency
from interview_app_backend.services.evaluation_signals import build_evaluation_context  # noqa: F401
from interview_app_backend.llm.client import get_openrouter_client
from config.settings import PRIMARY_PROVIDER


LOGGER = logging.getLogger(__name__)


def _get_single_provider_client():
    if PRIMARY_PROVIDER == "open-router":
        return get_openrouter_client()
    return get_openrouter_client()

def is_answer_relevant(question: str, answer: str, return_assessment: bool = False):
    from interview_app_backend.llm.client import call_llm
    from interview_app_backend.services.relevance_assessment import assess_relevance

    assessment = assess_relevance(question, answer, _get_single_provider_client, call_llm)
    if return_assessment:
        return assessment
    return assessment["status"] != "off_topic"


def build_overall_decision_detail(scores: Mapping[str, Any], trust_level: str = "high", score_confidence: float | int | None = None) -> dict[str, Any]:
    if not trust_level:
        trust_level = "low"
        score_confidence = 0.3
    score_based_value = derive_overall_decision(scores)
    detail_value = "borderline" if score_based_value == "borderline pass" else score_based_value
    score_confidence_level = confidence_level_from_value(score_confidence)
    decision_confidence = decision_confidence_from_trust(trust_level, score_confidence_level)
    reason = "Score-based decision retained."
    if trust_level == "medium":
        reason = "Decision retained with medium trust."
    elif trust_level == "low":
        reason = "Decision should be reviewed because trust level is low"
    return {
        "value": detail_value,
        "score_based_value": detail_value,
        "trust_level": trust_level,
        "score_confidence": score_confidence_level,
        "decision_confidence": decision_confidence,
        "gating_applied": False,
        "reason": reason,
    }


def build_normalisation(scores: Mapping[str, Any]) -> dict[str, Any]:
    return build_normalisation_detail(scores)


def validate_evaluation_consistency(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(evaluation)
    scores = dict(data.get("scores", {}))
    metrics_detected = bool(evaluation_context.get("metrics_detected") or evaluation_context.get("has_metrics") or evaluation_context.get("metric_count"))
    if evaluation_context.get("question_type", "behavioural") == "behavioural" and not metrics_detected and "specificity" in scores:
        scores["specificity"] = min(int(scores.get("specificity") or 0), 3)
        data["scores"] = scores
    result = apply_evaluation_consistency(data, evaluation_context)
    if result.get("validation_warnings"):
        LOGGER.warning("Evaluation contradictions and anomalies normalised: %s", "; ".join(result["validation_warnings"]))
    return result

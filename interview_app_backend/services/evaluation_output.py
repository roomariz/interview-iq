"""Keep candidate performance independent of evaluation reliability."""

from interview_app_backend.services.feedback_integrity import clean_feedback, memory_is_allowed
from interview_app_backend.services.evaluation_signals import TRUST_LEVEL_DEFINITIONS
from interview_app_backend.services.evaluation_rules import classify_fallback_failure, derive_overall_decision


RISK_CODES = {"unsupported_technology", "score_feedback_contradiction", "unsupported_metric_claim", "source_quote_mismatch"}


def finalise_evaluation(data):
    result = clean_feedback(data)
    trust = dict(result.get("trust", {}))
    warning = dict(result.get("validation_warning", {}))
    detail = dict(result.get("overall_decision_detail", {}))
    scores = result.get("scores", {})
    off_topic = bool(result.get("relevance_gate_applied") or not result.get("topic_match", True))
    confidence_values = [float(block["score_confidence"]) for block in (warning, trust)
                         if isinstance(block.get("score_confidence"), (int, float))]
    confidence = 0.0 if off_topic else max(0.0, min(1.0, min(confidence_values, default=0.0)))
    validation = result["feedback_validation"]
    issues = list(validation.get("issues", []))
    context = result.get("evaluation_context", {})
    flags = set(warning.get("anomaly_flags", [])) | set(context.get("anomaly_flags", []))
    risks = sorted({item["code"] for item in issues if item.get("code") in RISK_CODES}
                   | (flags & {"fake_metrics", "misleading_metrics"}))
    contradictions = warning.get("contradiction_flags", []) or context.get("contradiction_flags", [])
    issues.extend({"code": "extraction_consistency", "flag": flag} for flag in sorted(flags | set(contradictions)))
    if result.get("relevance_assessment", {}).get("status") == "uncertain":
        issues.append({"code": "uncertain_relevance"})
    if confidence < .45 and not off_topic:
        issues.append({"code": "low_score_support"})
    incomplete = not result.get("feedback", {}).get("strengths") and not off_topic
    if incomplete:
        issues.append({"code": "feedback_incomplete"})
    validation["issues"] = issues
    if incomplete and validation.get("status") == "checked":
        validation["status"] = "incomplete"
    level = "low" if confidence < .45 or risks or contradictions else "medium" if confidence < .78 or issues or flags else "high"
    if off_topic or result.get("relevance_assessment", {}).get("status") == "uncertain":
        level = "low"
    provisional = not off_topic and (level != "high" or incomplete or result.get("relevance_assessment", {}).get("status") == "uncertain")
    decision = "fail" if off_topic else derive_overall_decision(scores)
    decision_confidence = "high" if off_topic else "low" if level == "low" else level
    definition = ("Low evaluation depth but high decision confidence because the answer is not relevant to the question."
                  if off_topic else TRUST_LEVEL_DEFINITIONS[level])
    reason = ("The answer is not relevant to the question." if off_topic else
              "Score-based verdict retained; the assessment is provisional." if provisional else "Score-based verdict retained.")
    shared = dict(trust_level=level, trust_definition=definition, score_confidence=confidence)
    trust.update(shared, decision_confidence=decision_confidence, reason=reason)
    warning.update(shared, has_warning=bool(provisional or off_topic), interpretation=reason)
    warning["validation"] = {**warning.get("validation", {}), **shared}
    detail.update(shared, value=decision, score_based_value=decision, decision_confidence=decision_confidence,
                  gating_applied=off_topic, reason=reason)
    ec = dict(result.get("evaluation_confidence", {}))
    ec["grounding"] = confidence
    ec["overall"] = min(float(ec.get("relevance", confidence)), confidence)
    failure = "off_topic" if off_topic else "hallucination_risk" if risks else classify_fallback_failure(scores, True, False)
    result.update(trust=trust, validation_warning=warning, overall_decision_detail=detail,
                  score_confidence=confidence, grounding_score=confidence, overall_decision=decision,
                  evaluation_confidence=ec, failure_type=failure, failure_reasons=risks,
                  assessment_status="provisional" if provisional else "confirmed",
                  provisional=provisional, reliability_issues=issues)
    result["failure_scope"] = "evaluation_reliability" if risks else "answer_quality"
    result["confidence_definitions"] = {
        "score_confidence": "Evidence-extraction confidence after consistency penalties, 0–1; not candidate performance.",
        "relevance": "Semantic assessor confidence in its verdict, 0–1.",
        "completeness": "Observed evidence coverage, not confidence or a required rubric.",
        "overall": "Minimum of relevance and score confidence; does not change the performance verdict.",
        "decision_confidence": "Confidence in the verdict; confirmed off-topic may have high confidence with zero scoring depth.",
    }
    result["evaluation_summary"] = {
        "failure_type": failure, "reason": reason, "decision": decision,
        "confidence_label": level.capitalize(),
        "grounding_label": "Strong" if confidence >= .7 else "Partial" if confidence >= .4 else "Weak",
    }
    result["evaluation"] = {"overall_decision": decision, "scores": scores, "labels": result.get("labels", {})}
    result.setdefault("memory_storage_allowed", True)
    result["memory_storage_allowed"] = memory_is_allowed(result)
    result["memory_policy"] = "Withhold uncertain or unvalidated conclusions from memory."
    result["future_session_memory"] = []
    for stage in result.get("evaluation_pipeline", {}).get("stages", []):
        if stage.get("name") == "trust_calculator":
            stage["evaluation_confidence"] = ec
    for stale in ("key_takeaway", "trust_display", "reliability_card", "score_consistency"):
        result.pop(stale, None)
    return result

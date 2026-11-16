from collections.abc import Mapping

from interview_app_backend.services.evaluation_rules import derive_overall_decision
from interview_app_backend.services.trust_defaults import build_fallback_review_state


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _fallback_value(value: object, fallback: object) -> object:
    return value if value not in {None, ""} else fallback


def parse_prompt_contract(raw: Mapping[str, object]) -> dict:
    from interview_app_backend.llm.parser import EvaluationSchema

    evaluation = raw.get("evaluation") if isinstance(raw.get("evaluation"), Mapping) else {}
    scores = dict(evaluation.get("scores", {}))
    labels = dict(evaluation.get("labels", {}))
    summary = str(raw.get("summary", "")).strip()
    key_issues = _clean_list(raw.get("key_issues"))
    improvements = _clean_list(raw.get("improvements"))
    strengths = _clean_list(raw.get("strengths"))
    reasoning = raw.get("reasoning") if isinstance(raw.get("reasoning"), Mapping) else {}
    follow_up = raw.get("follow_up") if isinstance(raw.get("follow_up"), Mapping) else {}
    trust = raw.get("trust") if isinstance(raw.get("trust"), Mapping) else {}
    validation_warning_source = raw.get("validation_warning") if isinstance(raw.get("validation_warning"), Mapping) else {}
    fallback_state = build_fallback_review_state(
        scores,
        topic_match=bool(raw.get("topic_match", True)),
        relevance_gate_applied=bool(raw.get("relevance_gate_applied", False)),
        overall_decision=str(evaluation.get("overall_decision", "")).strip(),
    )
    legacy_payload = {
        "criteria": _clean_list(raw.get("criteria")),
        "evidence": {"metrics": [], "actions": [], "reasoning": ""},
        "scores": scores,
        "labels": labels,
        "feedback": {"summary": summary, "strengths": strengths, "key_issues": key_issues, "improvements": improvements},
        "reasoning": reasoning,
        "follow_up": follow_up,
        "example_answer": raw.get("example_answer", ""),
        "strengths": strengths,
        "improvement_areas": improvements,
        "overall_summary": summary,
        "evaluation_version": str(raw.get("evaluation_version", "")).strip(),
        "evaluation_trace": list(raw.get("evaluation_trace", [])) if isinstance(raw.get("evaluation_trace"), list) else [],
        "impact_strength": str(trust.get("impact_strength", "")).strip(),
    }
    result = EvaluationSchema.model_validate(legacy_payload).model_dump()
    overall_decision = str(evaluation.get("overall_decision") or derive_overall_decision(scores)).strip()
    trust_level = str(trust.get("trust_level", "")).strip()
    score_confidence = trust.get("score_confidence", 0.0)
    result["evaluation"] = {"overall_decision": overall_decision, "scores": result["scores"], "labels": result["labels"]}
    result["summary"] = summary
    result["key_issues"] = key_issues
    result["improvements"] = improvements
    result["topic_match"] = bool(raw.get("topic_match", True))
    result["relevance_gate_applied"] = bool(raw.get("relevance_gate_applied", False))
    result["failure_type"] = str(raw.get("failure_type", fallback_state["failure_type"])).strip() or fallback_state["failure_type"]
    trust_level = str(_fallback_value(trust.get("trust_level"), fallback_state["trust"]["trust_level"])).strip() or fallback_state["trust"]["trust_level"]
    score_confidence = _fallback_value(trust.get("score_confidence"), fallback_state["trust"]["score_confidence"])
    decision_confidence = str(_fallback_value(trust.get("decision_confidence"), fallback_state["trust"]["decision_confidence"])).strip() or fallback_state["trust"]["decision_confidence"]
    trust_definition = str(_fallback_value(trust.get("trust_definition"), fallback_state["trust"]["trust_definition"])).strip() or fallback_state["trust"]["trust_definition"]
    reason = str(_fallback_value(trust.get("reason"), fallback_state["trust"]["reason"])).strip() or fallback_state["trust"]["reason"]
    impact_strength = str(_fallback_value(trust.get("impact_strength"), fallback_state["trust"]["impact_strength"])).strip() or fallback_state["trust"]["impact_strength"]
    result["trust"] = {
        "trust_level": trust_level,
        "trust_definition": trust_definition,
        "score_confidence": score_confidence,
        "decision_confidence": decision_confidence,
        "impact_strength": impact_strength,
        "reason": reason,
    }
    result["feedback"] = {"summary": summary, "strengths": strengths, "key_issues": key_issues, "improvements": improvements}
    result["overall_decision"] = overall_decision
    result["overall_summary"] = summary
    result["validation_warning"] = {
        **fallback_state["validation_warning"],
        "has_warning": result["relevance_gate_applied"] or fallback_state["validation_warning"]["has_warning"] or trust_level in {"low", "medium"},
        "severity": str(_fallback_value(validation_warning_source.get("severity"), fallback_state["validation_warning"]["severity"])).strip() or fallback_state["validation_warning"]["severity"],
        "trust_level": str(_fallback_value(validation_warning_source.get("trust_level"), trust_level)).strip() or trust_level,
        "score_confidence": score_confidence if score_confidence else fallback_state["validation_warning"]["score_confidence"],
        "reasoning_depth": str(_fallback_value(validation_warning_source.get("reasoning_depth"), fallback_state["validation_warning"]["reasoning_depth"])).strip() or fallback_state["validation_warning"]["reasoning_depth"],
        "interpretation": str(_fallback_value(validation_warning_source.get("interpretation"), fallback_state["validation_warning"]["interpretation"])).strip() or fallback_state["validation_warning"]["interpretation"],
    }
    if result["failure_type"] == "off_topic":
        result["validation_warning"]["severity"] = "info"
        result["validation_warning"]["reasoning_depth"] = "not_applicable"
        result["validation_warning"]["interpretation"] = "This answer is not relevant to the question, so detailed evaluation is not applicable."
    result["overall_decision_detail"] = {
        **fallback_state["overall_decision_detail"],
        "value": overall_decision,
        "score_based_value": overall_decision,
        "trust_level": trust_level or fallback_state["overall_decision_detail"]["trust_level"],
        "score_confidence": score_confidence if score_confidence else fallback_state["overall_decision_detail"]["score_confidence"],
        "decision_confidence": str(trust.get("decision_confidence", fallback_state["overall_decision_detail"]["decision_confidence"])).strip() or fallback_state["overall_decision_detail"]["decision_confidence"],
        "gating_applied": bool(raw.get("relevance_gate_applied", False)) or fallback_state["overall_decision_detail"]["gating_applied"],
        "reason": str(trust.get("reason", fallback_state["overall_decision_detail"]["reason"])).strip() or fallback_state["overall_decision_detail"]["reason"],
    }
    result["evaluation_version"] = str(raw.get("evaluation_version", result.get("evaluation_version", ""))).strip()
    result["evaluation_trace"] = list(raw.get("evaluation_trace", result.get("evaluation_trace", []))) if isinstance(raw.get("evaluation_trace"), list) else result.get("evaluation_trace", [])
    result["impact_strength"] = str(trust.get("impact_strength", result.get("impact_strength", ""))).strip()
    return result

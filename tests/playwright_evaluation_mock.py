from __future__ import annotations

from interview_app_backend.services.evaluation_interpretation import build_validation_warning
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation
from interview_app_backend.services.trust_defaults import build_fallback_review_state


QUESTION = (
    "Describe a time you improved system performance under constraints. "
    "Include the challenge, your approach, and measurable results."
)


def _build_payload(
    question: str,
    answer: str,
    scores: dict[str, int],
    labels: dict[str, str],
    summary: dict[str, str],
    key_issues: list[str],
    improvements: list[str],
    strengths: list[str],
    reasoning: dict[str, str],
    follow_up: dict[str, str],
    decision: str,
    failure_type: str,
    example_answer: str = "",
) -> dict[str, object]:
    review_state = build_fallback_review_state(scores, topic_match=True, relevance_gate_applied=False, overall_decision=decision)
    review_state["validation_warning"]["interpretation"] = summary["interpretation"]
    review_state["validation_warning"]["severity"] = summary["severity"]
    review_state["validation_warning"]["reasoning_depth"] = summary["reasoning_depth"]
    review_state["overall_decision_detail"]["value"] = decision
    review_state["overall_decision_detail"]["score_based_value"] = decision
    review_state["trust"]["decision_confidence"] = summary["decision_confidence"]
    review_state["trust"]["reason"] = summary["trust_reason"]
    payload: dict[str, object] = {
        "question": question,
        "answer": answer,
        "overall_decision": decision,
        "scores": scores,
        "labels": labels,
        "summary": summary["summary"],
        "key_issues": key_issues,
        "improvements": improvements,
        "strengths": strengths,
        "criteria": [
            "Problem-solving clarity and approach",
            "Ownership and impact",
            "Communication and structure (STAR)",
            "Technical depth and trade-offs",
        ],
        "reasoning": reasoning,
        "follow_up": follow_up,
        "topic_match": True,
        "relevance_gate_applied": False,
        "failure_type": failure_type,
        "memory_storage_allowed": True,
        "future_session_memory": [],
        "example_answer": example_answer,
        "evaluation_summary": {
            "confidence_label": summary["confidence_label"],
            "grounding_label": summary["grounding_label"],
            "failure_type": failure_type,
            "reason": summary["summary"],
            "decision": decision,
        },
        "evaluation_confidence": {"relevance": 0.7, "grounding": 0.6, "completeness": 0.6, "overall": 0.63, "conflict": False},
    }
    payload.update(review_state)
    payload["overall_decision_detail"]["value"] = decision
    payload["overall_decision_detail"]["score_based_value"] = decision
    payload["validation_warning"]["interpretation"] = summary["interpretation"]
    payload["validation_warning"]["severity"] = summary["severity"]
    payload["validation_warning"]["reasoning_depth"] = summary["reasoning_depth"]
    payload["trust"]["decision_confidence"] = summary["decision_confidence"]
    payload["trust"]["reason"] = summary["trust_reason"]
    return payload


def _sanitize_off_topic(question: str, answer: str) -> dict[str, object]:
    payload = build_relevance_gate_evaluation(question, answer)
    payload["feedback"] = {
        "summary": "The answer is not relevant to the question, so only broad guidance is appropriate.",
        "strengths": [],
        "key_issues": ["The answer is not relevant to the system performance question."],
        "improvements": ["Give a real example about improving system performance under constraints."],
    }
    payload["reasoning"] = {
        "clarity": "The response is understandable, but it does not answer the asked question.",
        "alternative_approaches": "No alternatives are discussed because the answer is not relevant to the question.",
        "trade_off_awareness": "No further technical detail is grounded in the answer.",
        "evidence": "Only broad guidance is appropriate because there is no relevant technical evidence to assess.",
    }
    payload["example_answer"] = ""
    payload["evaluation_summary"] = {"confidence_label": "Low", "grounding_label": "Weak", "failure_type": "off_topic", "reason": "The answer is not relevant to the question.", "decision": "fail"}
    payload["validation_warning"]["interpretation"] = "The answer is not relevant to the question, so the fail result is reliable."
    return payload


def _ok(question: str, answer: str) -> dict[str, object]:
    return _build_payload(
        question,
        answer,
        {"relevance": 7, "structure": 4, "specificity": 4, "communication": 7, "problem_solving_approach": 5},
        {"relevance": "Addresses the question directly", "structure": "Weak structure", "specificity": "Missing metrics", "communication": "Clear and easy to follow", "problem_solving_approach": "Reasoning is present, but it is thin"},
        {"confidence_label": "Medium", "grounding_label": "Partial", "interpretation": "Use with caution; the evidence is incomplete.", "severity": "medium", "reasoning_depth": "developing", "decision_confidence": "medium", "trust_reason": "The answer is on topic, but the evidence is incomplete.", "summary": "The answer is on topic, but the structure is incomplete and the metrics are missing."},
        ["The answer stays relevant to system performance."],
        ["Missing metrics", "Weak structure"],
        ["Add one concrete metric in ms or %.", "Reshape the answer into challenge, approach, and result."],
        ["Addresses the question directly", "Clear and easy to follow", "Needs more concrete evidence"],
        {"clarity": "The answer is readable, but the structure is incomplete.", "alternative_approaches": "No alternative is explained.", "trade_off_awareness": "No trade-offs are stated.", "evidence": "No concrete metric is provided."},
        {"question": "How would you add one concrete metric and a clearer structure?", "type": "depth_probe", "target_dimension": "specificity", "reasoning_action": "Add one rejected option and one trade-off you accepted.", "context_note": "Grounded in metrics and structure.", "stage": 1},
        "borderline pass",
        "low_specificity",
        "A relevant answer is present, but it lacks concrete evidence.",
        "A stronger answer would reference a measurable result in ms or %.",
    )


def _good(question: str, answer: str) -> dict[str, object]:
    return _build_payload(
        question,
        answer,
        {"relevance": 8, "structure": 6, "specificity": 7, "communication": 7, "problem_solving_approach": 6},
        {"relevance": "Addresses the question directly", "structure": "Partial structure", "specificity": "Metrics are present, but the evidence could be clearer", "communication": "Clear and easy to follow", "problem_solving_approach": "The reasoning is present, but it needs one explicit trade-off"},
        {"confidence_label": "Medium", "grounding_label": "Partial", "interpretation": "Use with caution; the evidence is partial.", "severity": "medium", "reasoning_depth": "developing", "decision_confidence": "medium", "trust_reason": "The answer is broadly supported, but the metrics and reasoning could be stronger.", "summary": "Metrics are present, but the answer still needs one concrete figure in ms and a clearer explanation of the reasoning."},
        ["The answer mentions the performance problem and stays on topic."],
        ["Add one latency figure in ms or a percentage.", "State the decision you made and why."],
        ["Addresses the question directly", "Mentions latency", "Shows some reasoning"],
        {"clarity": "The approach is understandable, but one decision still needs to be justified.", "alternative_approaches": "Name one alternative and why it was not chosen.", "trade_off_awareness": "Mention the trade-off between speed and operational complexity.", "evidence": "Latency is the metric signal here; add one concrete figure in ms."},
        {"question": "How would you make the latency result more concrete?", "type": "depth_probe", "target_dimension": "specificity", "reasoning_action": "Add one rejected option and one trade-off you accepted.", "context_note": "Grounded in metrics and impact.", "stage": 1},
        "pass",
        "low_evidence",
        "A relevant answer is present, but the evidence is still thin.",
        "A stronger answer would sound like: latency improved from 120ms to 400ms.",
    )


def _best(question: str, answer: str) -> dict[str, object]:
    return _build_payload(
        question,
        answer,
        {"relevance": 9, "structure": 8, "specificity": 9, "communication": 8, "problem_solving_approach": 8},
        {"relevance": "Addresses the question directly", "structure": "Clear sections are present", "specificity": "Metrics are present and concrete", "communication": "Clear and easy to follow", "problem_solving_approach": "The answer explains why the choice was made"},
        {"confidence_label": "High", "grounding_label": "Strong", "interpretation": "Use normally; the evidence is strong.", "severity": "low", "reasoning_depth": "explicit", "decision_confidence": "high", "trust_reason": "The answer is well supported by explicit metrics and trade-offs.", "summary": "Clear before/after metrics are present, and the trade-off is explicit."},
        ["The answer could mention one longer-term operational detail."],
        ["Keep the concise structure, and briefly call out the operational trade-off."],
        ["Addresses the question directly", "Clear and easy to follow", "Metrics are concrete"],
        {"clarity": "The approach is clear and the result is measurable.", "alternative_approaches": "A sensible alternative is implicitly acknowledged.", "trade_off_awareness": "The latency trade-off is explicit.", "evidence": "The answer includes before/after latency numbers (120ms to 400ms)."},
        {"question": "What trade-off did you accept to get the latency down?", "type": "depth_probe", "target_dimension": "problem_solving_approach", "reasoning_action": "Summarise the trade-off and the impact in one crisp closing sentence.", "context_note": "Grounded in trade-offs and alternatives.", "stage": 1},
        "pass",
        "none",
        "The backend optimisation result is specific and well supported.",
    )


def evaluate_submission(question: str, answer: str) -> dict[str, object]:
    lowered = answer.lower()
    if "documentation" in lowered or "collaboration" in lowered:
        return _sanitize_off_topic(question, answer)
    if "120ms" in lowered and "400ms" in lowered:
        return _best(question, answer)
    if "latency increased" in lowered:
        return _good(question, answer)
    return _ok(question, answer)


def patch() -> None:
    import interview_app_backend.services.evaluation_service as service

    service.evaluate_submission = evaluate_submission

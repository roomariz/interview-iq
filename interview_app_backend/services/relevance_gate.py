from interview_app_backend.services.evaluation_interpretation import build_validation_warning
from interview_app_backend.services.evaluation_rules import build_normalisation

RELEVANCE_GATE_VERSION = "relevance-gate-v2"


def build_relevance_gate_evaluation(question: str, answer: str) -> dict:
    intent = question
    scores = {
        "technical_accuracy": 1,
        "clarity": 6,
        "structure": 3,
        "relevance": 1,
        "problem_solving_approach": 2,
        "specificity": 1,
        "communication": 6,
    }
    evaluation_context = {
        "evaluation_version": RELEVANCE_GATE_VERSION,
        "evaluation_trace": [f"version:{RELEVANCE_GATE_VERSION}", "hard_relevance_gate:triggered", f"question_intent:{intent}"],
        "has_metrics": False,
        "metrics_detected": False,
        "metric_count": 0,
        "has_structure": False,
        "has_reasoning": False,
        "has_tradeoffs": False,
        "has_alternatives": False,
        "confidence": {"metrics": 0.0, "structure": 0.0, "reasoning": 0.0, "tradeoffs": 0.0, "alternatives": 0.0},
        "contradiction_flags": ["relevance_contradiction"],
        "anomaly_flags": ["off_topic_answer"],
        "numeric_signals": [],
        "impact_strength": "weak",
        "topic_match": False,
        "relevance_score": scores["relevance"],
    }
    evaluation = {
        "evidence": {"metrics": [], "actions": [], "reasoning": ""},
        "scores": scores,
        "labels": {
            "relevance": "Does not address the original question",
            "structure": "Not assessed because the answer is off-topic",
            "specificity": "No evidence addressing the original question provided",
            "communication": "Clear but not relevant to the question",
            "problem_solving_approach": "No relevant technical problem-solving demonstrated",
        },
        "feedback": {
            "summary": (
                f"The answer is not relevant to the question about {intent}. "
                "I cannot assess technical approach, because the response stays off topic."
            ),
            "strengths": [],
            "key_issues": ["The response addresses a different subject from the original question."],
            "improvements": [f"Address the original question directly: {question}"],
        },
        "reasoning": {
            "clarity": "The response is readable, but it does not answer the asked question.",
            "alternative_approaches": "No alternatives are discussed because the answer is not relevant to the question.",
            "trade_off_awareness": "No constraints or trade-offs are grounded in the answer.",
            "evidence": "There is no relevant technical evidence to assess.",
        },
        "follow_up": {
            "question": f"Please address the original question directly: {question}",
            "type": "relevance_gate",
            "target_dimension": "relevance",
            "reasoning_action": "Address the substance of the original question.",
            "context_note": f"Grounded in the original question about {intent}.",
            "stage": 1,
        },
        "example_answer": {},
        "strengths": [],
        "improvement_areas": [f"Address the original question directly: {question}"],
        "overall_summary": (
            f"The answer is not relevant to the question about {intent}, so the technical evaluation cannot be trusted."
        ),
        "evaluation_version": RELEVANCE_GATE_VERSION,
        "evaluation_trace": evaluation_context["evaluation_trace"],
        "impact_strength": "weak",
        "topic_match": False,
        "relevance_gate_applied": True,
        "memory_storage_allowed": False,
        "hard_relevance_gate": True,
        "failure_type": "off_topic",
        "answer": answer,
        "question": question,
        "evaluation_context": evaluation_context,
    }
    warning = build_validation_warning(evaluation, evaluation_context, {"relevance": ["relevance_contradiction"]})
    warning["severity"] = "info"
    warning["severity_definition"] = "Expected behaviour; the answer is not relevant to the question."
    warning["trust_level"] = "low"
    warning["trust_definition"] = "Low confidence in detailed feedback, but high confidence in the decision."
    warning["score_confidence"] = 0.0
    warning["interpretation"] = "The answer does not address the question, so only high-level guidance is provided."
    warning["validation"]["severity"] = "info"
    warning["validation"]["severity_definition"] = warning["severity_definition"]
    warning["validation"]["trust_level"] = "low"
    warning["validation"]["score_confidence"] = 0.0
    warning["validation"]["trust_definition"] = warning["trust_definition"]
    warning["reasoning"]["reasoning_depth"] = "not_applicable"
    warning["reasoning"]["reasoning_depth_definition"] = "Reasoning is not applicable because the answer is not relevant to the question."
    warning["has_warning"] = True
    warning["grouped_anomaly_flags"] = {"numeric": [], "directional": [], "non_impact": []}
    evaluation["validation_warning"] = warning
    evaluation["validation_warnings"] = [warning["interpretation"]]
    evaluation["overall_decision"] = "fail"
    evaluation["overall_decision_detail"] = {
        "value": "fail",
        "score_based_value": "fail",
        "trust_level": "low",
        "score_confidence": "low",
        "decision_confidence": "high",
        "gating_applied": False,
        "reason": "The answer is clearly off topic, so the fail decision is reliable, but deeper evaluation is limited.",
    }
    evaluation["normalisation"] = build_normalisation(scores)
    evaluation["normalised_score_detail"] = evaluation["normalisation"].get("detail")
    return evaluation

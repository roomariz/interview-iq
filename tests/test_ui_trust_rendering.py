import json
import pytest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import build_behaviour_aware_trust, build_score_consistency


QUESTION = "Describe a time you improved system performance under constraints."


def _scores(relevance, structure, specificity, communication, problem_solving_approach):
    return {
        "technical_accuracy": specificity,
        "clarity": communication,
        "structure": structure,
        "relevance": relevance,
        "problem_solving_approach": problem_solving_approach,
        "specificity": specificity,
        "communication": communication,
    }


def _payload(scores, reasoning_depth="none", trust_level="medium", labels=None, key_issues=None, improvements=None, strengths=None, summary="Summary."):
    return {
        "evidence": {"metrics": [], "actions": [], "reasoning": ""},
        "scores": scores,
        "labels": labels or {key: "" for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")},
        "feedback": {"summary": summary, "strengths": strengths or [], "key_issues": key_issues or [], "improvements": improvements or []},
        "reasoning": {"clarity": "", "alternative_approaches": "", "trade_off_awareness": "", "evidence": ""},
        "follow_up": {"question": "", "type": "", "target_dimension": ""},
        "example_answer": {},
        "strengths": strengths or [],
        "improvement_areas": improvements or [],
        "overall_summary": summary,
        "evaluation_version": "trust-v4",
        "evaluation_trace": ["version:trust-v4"],
        "impact_strength": "weak",
        "reasoning_depth": reasoning_depth,
        "trust_level": trust_level,
    }


def _evaluate(answer, context, payload, relevant=True):
    support = {"feedback_support": [
        {"claim": claim, "answer_quote": answer, "question_quote": QUESTION}
        for key in ("strengths", "key_issues", "improvements")
        for claim in payload.get("feedback", {}).get(key, [])
    ]}
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=relevant), patch(
        "interview_app_backend.services.evaluation_service.get_openrouter_client", return_value=object()
    ), patch(
        "interview_app_backend.services.evaluation_service.call_llm", return_value=json.dumps(support)
    ), patch(
        "interview_app_backend.services.evaluation_service.generate_reference_answer", return_value="Reference answer."
    ), patch("interview_app_backend.services.evaluation_service.calculate_semantic_similarity", return_value=0.88), patch(
        "interview_app_backend.services.evaluation_service.extract_evidence_context", return_value=context
    ), patch("interview_app_backend.services.evaluation_service.parse_json_response", return_value=payload):
        return evaluate_submission(QUESTION, answer)


class TestUITrustRendering:
    def test_confidence_label_renders_for_high_trust(self):
        payload = _payload(
            _scores(9, 9, 9, 9, 8),
            reasoning_depth="deep",
            trust_level="high",
            strengths=["Strong metrics", "Clear reasoning"],
            summary="Excellent answer."
        )
        result = _evaluate(
            "I reduced latency from 400ms to 80ms by profiling hot paths, identifying the N+1 query, and adding appropriate indexes.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": True, "confidence": {"metrics": 0.95, "structure": 0.9, "reasoning": 0.9, "tradeoffs": 0.85, "alternatives": 0.8}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["400ms", "80ms"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert "decision" in trust
        assert "high" in trust["decision"].lower()

    def test_confidence_label_renders_for_low_trust(self):
        payload = _payload(
            _scores(7, 6, 5, 6, 4),
            reasoning_depth="none",
            trust_level="low",
            key_issues=["Strong scores but weak evidence"],
            summary="Scores and evidence are misaligned."
        )
        result = _evaluate(
            "I improved the system significantly with great results.",
            {"has_metrics": False, "metrics": [], "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.2, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": ["metrics_contradiction"], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert "decision" in trust
        assert "low" in trust["decision"].lower() or "caution" in trust["summary"].lower() or "limited" in trust["summary"].lower()

    def test_grounding_label_renders(self):
        payload = _payload(
            _scores(8, 7, 8, 7, 6),
            reasoning_depth="developing",
            trust_level="medium",
            summary="Good answer."
        )
        result = _evaluate(
            "I reduced response time from 300ms to 120ms by adding caching and optimising queries.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.7, "reasoning": 0.6, "tradeoffs": 0.3, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["300ms", "120ms"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert "grounding" in trust or "detail" in trust

    def test_assessment_text_renders_for_strong_answer(self):
        payload = _payload(
            _scores(9, 9, 9, 9, 8),
            reasoning_depth="explicit",
            trust_level="high",
            strengths=["Strong evidence", "Clear metrics"],
            summary="Excellent answer with strong evidence."
        )
        result = _evaluate(
            "I led a performance optimisation effort. I profiled the system, identified the bottleneck, and implemented a solution that reduced latency from 500ms to 50ms.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": True, "confidence": {"metrics": 0.95, "structure": 0.9, "reasoning": 0.9, "tradeoffs": 0.85, "alternatives": 0.8}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["500ms", "50ms"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert "depth" in trust
        assert "explicit" in trust["depth"].lower() or "high" in trust["decision"].lower()

    def test_assessment_text_renders_for_weak_answer(self):
        payload = _payload(
            _scores(5, 4, 3, 5, 3),
            reasoning_depth="implicit",
            trust_level="low",
            key_issues=["No specific metrics", "Vague outcome"],
            improvements=["Add concrete numbers"],
            summary="Weak answer lacks evidence."
        )
        result = _evaluate(
            "I made the system faster.",
            {"has_metrics": False, "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.2, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert "depth" in trust
        assert "implicit" in trust["depth"].lower() or "low" in trust["decision"].lower()

    def test_trust_summary_not_empty(self):
        payload = _payload(
            _scores(7, 7, 7, 7, 6),
            reasoning_depth="developing",
            trust_level="medium",
            summary="Good answer."
        )
        result = _evaluate(
            "I reduced latency by implementing caching and query optimisation.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.7, "structure": 0.7, "reasoning": 0.6, "tradeoffs": 0.3, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "moderate"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert trust["summary"].strip()
        assert len(trust["summary"]) > 10

    def test_trust_detail_not_empty(self):
        payload = _payload(
            _scores(8, 8, 8, 8, 7),
            reasoning_depth="developing",
            trust_level="high",
            summary="Strong answer."
        )
        result = _evaluate(
            "I reduced response time by 50% through caching and query optimisation.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.5, "alternatives": 0.3}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["50%"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert trust["detail"].strip()
        assert len(trust["detail"]) > 10
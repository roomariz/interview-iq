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


def _payload(scores, labels=None, key_issues=None, improvements=None, strengths=None, summary="Summary.", reasoning_depth="none", trust_level="medium"):
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
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=relevant), patch(
        "interview_app_backend.services.evaluation_service.get_openrouter_client", return_value=object()
    ), patch(
        "interview_app_backend.services.evaluation_service.call_llm", return_value="{}"
    ), patch(
        "interview_app_backend.services.evaluation_service.generate_reference_answer", return_value="Reference answer."
    ), patch("interview_app_backend.services.evaluation_service.calculate_semantic_similarity", return_value=0.88), patch(
        "interview_app_backend.services.evaluation_service.extract_evidence_context", return_value=context
    ), patch("interview_app_backend.services.evaluation_service.parse_json_response", return_value=payload):
        return evaluate_submission(QUESTION, answer)


class TestTrustConsistency:
    def test_trust_level_aligns_with_reliability_card(self):
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

        assert result["validation_warning"]["trust_level"] == "high"
        assert "high" in trust["summary"].lower() or "strong" in trust["summary"].lower() or "provisional" not in trust["summary"].lower()

    def test_low_trust_shows_reliability_warning(self):
        payload = _payload(
            _scores(8, 8, 8, 8, 8),
            reasoning_depth="none",
            trust_level="low",
            key_issues=["High scores but weak evidence"],
            summary="Scores and evidence are misaligned."
        )
        result = _evaluate(
            "I improved the system significantly with great results.",
            {"has_metrics": False, "metrics": [], "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.2, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": ["metrics_contradiction"], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        trust = build_behaviour_aware_trust(view)

        assert result["validation_warning"]["trust_level"] == "low"
        assert "low" in trust["decision"].lower() or "provisional" in trust["summary"].lower() or "caution" in trust["summary"].lower()

    def test_decision_confidence_aligns_with_failure_type(self):
        off_topic_payload = _payload(_scores(1, 1, 1, 5, 1))
        result_off_topic = _evaluate(
            "I like to bake cookies on weekends.",
            {"has_metrics": False, "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.0, "structure": 0.0, "reasoning": 0.0, "tradeoffs": 0.0, "alternatives": 0.0}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": False, "impact_strength": "weak"},
            off_topic_payload,
            relevant=False
        )

        assert result_off_topic["overall_decision"] == "fail"
        assert result_off_topic["overall_decision_detail"]["decision_confidence"] in ["high"]
        assert result_off_topic["failure_type"] == "off_topic" or result_off_topic["validation_warning"]["trust_level"] == "low"

    def test_no_contradictory_signals_in_strong_answer(self):
        payload = _payload(
            _scores(8, 8, 8, 8, 7),
            reasoning_depth="developing",
            trust_level="high",
            strengths=["Clear metrics", "Good structure"],
            summary="Strong answer."
        )
        result = _evaluate(
            "I reduced response time from 300ms to 120ms by adding a cache layer and optimising queries.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.6, "alternatives": 0.3}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["300ms", "120ms"], "topic_match": True, "impact_strength": "strong"},
            payload
        )

        assert result["validation_warning"]["trust_level"] in ["medium", "high"]
        assert result["overall_decision_detail"]["decision_confidence"] in ["medium", "high"]

        anomaly_flags = result["validation_warning"].get("anomaly_flags", [])
        contradiction_flags = result.get("contradiction_flags", [])

        assert "misleading_metrics" not in anomaly_flags
        assert "metrics_contradiction" not in contradiction_flags

    def test_borderline_answer_has_appropriate_confidence(self):
        payload = _payload(
            _scores(5, 5, 4, 5, 4),
            reasoning_depth="implicit",
            trust_level="medium",
            key_issues=["Missing specific metrics", "Vague outcome"],
            improvements=["Add concrete numbers to demonstrate impact"],
            summary="Borderline relevant but lacks evidence."
        )
        result = _evaluate(
            "I improved the service by making it faster.",
            {"has_metrics": False, "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.2, "structure": 0.4, "reasoning": 0.2, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )

        assert result["overall_decision"] in ["borderline pass", "fail"]
        assert result["validation_warning"]["trust_level"] in ["low", "medium"]

    def test_trust_and_decision_confidence_consistency(self):
        high_trust_payload = _payload(
            _scores(9, 9, 9, 9, 9),
            reasoning_depth="deep",
            trust_level="high",
            summary="Excellent answer."
        )
        result = _evaluate(
            "I led a performance optimisation effort. I profiled the system, identified the bottleneck, and implemented a solution that reduced latency from 500ms to 50ms, improving user experience significantly.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": True, "confidence": {"metrics": 0.95, "structure": 0.95, "reasoning": 0.95, "tradeoffs": 0.9, "alternatives": 0.85}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["500ms", "50ms"], "topic_match": True, "impact_strength": "strong"},
            high_trust_payload
        )

        decision_confidence = result["overall_decision_detail"].get("decision_confidence", "low")

        if result["validation_warning"]["trust_level"] == "high":
            assert decision_confidence in ["high", "medium"]
        elif result["validation_warning"]["trust_level"] == "low":
            assert decision_confidence in ["low", "medium"]
import pytest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission


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


def _payload(scores, reasoning_depth="none", trust_level="low", labels=None, key_issues=None, improvements=None, strengths=None, summary="Summary."):
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


class TestCalibrationLevels:
    def test_weak_answer_yields_borderline_pass_or_fail(self):
        payload = _payload(
            _scores(5, 4, 3, 5, 3),
            reasoning_depth="none",
            trust_level="low",
            key_issues=["No specific metrics provided", "Vague outcome description"],
            improvements=["Add measurable results", "Describe the specific bottleneck"],
            summary="Answer lacks concrete evidence."
        )
        result = _evaluate(
            "I improved the system performance by optimising the code.",
            {"has_metrics": False, "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.3, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        assert result["overall_decision"] in ["borderline pass", "fail"]
        assert result["validation_warning"]["trust_level"] in ["low", "medium"]
        assert result["validation_warning"]["reasoning_depth"] in ["none", "implicit"]

    def test_good_answer_yields_pass_or_borderline_medium_confidence(self):
        payload = _payload(
            _scores(7, 7, 7, 7, 6),
            reasoning_depth="developing",
            trust_level="medium",
            key_issues=["Could mention alternative approaches"],
            improvements=["Discuss one alternative approach you considered"],
            summary="Good answer with solid evidence."
        )
        result = _evaluate(
            "I reduced API latency from 300ms to 150ms by adding caching and optimising the database query.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.7, "reasoning": 0.6, "tradeoffs": 0.3, "alternatives": 0.3}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["300ms", "150ms"], "topic_match": True, "impact_strength": "moderate"},
            payload
        )
        assert result["overall_decision"] in ["pass", "borderline pass"]
        assert result["validation_warning"]["trust_level"] in ["medium", "high"]
        assert result["overall_decision_detail"]["decision_confidence"] in ["medium", "high"]

    def test_best_answer_yields_pass_high_confidence(self):
        payload = _payload(
            _scores(9, 9, 9, 9, 8),
            reasoning_depth="deep",
            trust_level="high",
            key_issues=["Consider mentioning one more alternative"],
            strengths=["Clear STAR structure", "Strong metrics", "Good trade-off discussion"],
            summary="Excellent answer with comprehensive evidence."
        )
        result = _evaluate(
            "I led a three-month optimisation effort because latency was affecting users. I compared two alternatives - sharding vs caching - and chose caching for lower risk. I reduced latency from 400ms to 80ms by adding Redis caching and optimising the hot path. This improved user experience and reduced server load by 40%.",
            {"has_metrics": True, "metrics": [{"type": "latency"}, {"type": "load"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": True, "reasoning_markers": ["because"], "tradeoff_markers": ["trade-off", "lower risk"], "alternative_markers": ["compared", "alternatives"], "confidence": {"metrics": 0.95, "structure": 0.9, "reasoning": 0.9, "tradeoffs": 0.85, "alternatives": 0.8}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["400ms", "80ms", "40%"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        assert result["overall_decision"] == "pass"
        assert result["validation_warning"]["trust_level"] == "high"
        assert result["validation_warning"]["reasoning_depth"] == "deep"
        assert result["overall_decision_detail"]["decision_confidence"] == "high"

    def test_no_metrics_yields_medium_or_low_confidence(self):
        payload = _payload(
            _scores(6, 6, 5, 6, 5),
            reasoning_depth="implicit",
            trust_level="medium",
            key_issues=["No specific metrics provided"],
            summary="Relevant but lacks measurable outcomes."
        )
        result = _evaluate(
            "I improved system performance by identifying bottlenecks and implementing solutions.",
            {"has_metrics": False, "metrics": [], "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.5, "reasoning": 0.2, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        assert result["validation_warning"]["trust_level"] in ["low", "medium"]

    def test_metrics_present_yields_higher_confidence(self):
        payload = _payload(
            _scores(8, 7, 8, 7, 6),
            reasoning_depth="developing",
            trust_level="medium",
            key_issues=["Could elaborate on trade-offs"],
            summary="Good answer with clear metrics."
        )
        result = _evaluate(
            "I reduced query time from 500ms to 100ms by adding an index.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.7, "reasoning": 0.6, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["500ms", "100ms"], "topic_match": True, "impact_strength": "strong"},
            payload
        )
        assert result["validation_warning"]["trust_level"] in ["medium", "high"]

    def test_reasoning_depth_affects_trust_level(self):
        payload_no_reasoning = _payload(
            _scores(7, 6, 7, 6, 5),
            reasoning_depth="none",
            trust_level="low",
            summary="Has metrics but no reasoning."
        )
        result_no_reasoning = _evaluate(
            "I reduced latency from 200ms to 100ms.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.3, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["200ms", "100ms"], "topic_match": True, "impact_strength": "moderate"},
            payload_no_reasoning
        )

        payload_with_reasoning = _payload(
            _scores(7, 6, 7, 6, 6),
            reasoning_depth="developing",
            trust_level="medium",
            summary="Has metrics and some reasoning."
        )
        result_with_reasoning = _evaluate(
            "I reduced latency from 200ms to 100ms by profiling the hot path and identifying the N+1 query issue.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.6, "reasoning": 0.5, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["200ms", "100ms"], "topic_match": True, "impact_strength": "strong"},
            payload_with_reasoning
        )

        trust_no_reasoning = result_no_reasoning["validation_warning"]["trust_level"]
        trust_with_reasoning = result_with_reasoning["validation_warning"]["trust_level"]

        assert trust_with_reasoning in ["medium", "high"]
        assert trust_no_reasoning in ["low", "medium"]
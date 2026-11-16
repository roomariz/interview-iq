import unittest
from unittest.mock import patch

from interview_app_backend.services.evaluation_calibration import build_normalisation_detail, get_calibration_dataset, validate_calibration_dataset
from interview_app_backend.services.evaluation_grounding import ground_evaluation_result
from interview_app_backend.services.evaluation_interpretation import build_validation_warning
from interview_app_backend.services.evaluation_rules import build_overall_decision_detail, derive_overall_decision
from interview_app_backend.services.evaluation_service import evaluate_answer
from interview_app_backend.services.evaluation_signals import classify_reasoning_depth


class TestEvaluationRefinements(unittest.TestCase):
    def test_calibration_dataset_is_present_and_valid(self) -> None:
        dataset = get_calibration_dataset()
        self.assertTrue(validate_calibration_dataset())
        self.assertEqual(len(dataset), 6)
        self.assertIn("excellent_metrics_reasoning", {case["id"] for case in dataset})
        self.assertTrue(all(case["expected_score_band"] in {"excellent", "good", "borderline", "weak"} for case in dataset))

    def test_reasoning_depth_scale_covers_all_levels(self) -> None:
        self.assertEqual(classify_reasoning_depth({"scores": {"problem_solving_approach": 0}}, {"has_reasoning": False, "action_count": 0}), "none")
        self.assertEqual(classify_reasoning_depth({"scores": {"problem_solving_approach": 3}}, {"has_reasoning": False, "action_count": 1}), "implicit")
        self.assertEqual(classify_reasoning_depth({"scores": {"problem_solving_approach": 4}}, {"has_reasoning": True, "action_count": 0}), "developing")
        self.assertEqual(classify_reasoning_depth({"scores": {"problem_solving_approach": 7}}, {"has_reasoning": True, "reasoning_markers": ["because"], "tradeoff_markers": [], "alternative_markers": []}), "explicit")
        self.assertEqual(classify_reasoning_depth({"scores": {"problem_solving_approach": 8}}, {"has_reasoning": True, "reasoning_markers": ["because"], "tradeoff_markers": ["trade-off"], "alternative_markers": ["alternatives"]}), "deep")

    def test_machine_readable_anomaly_influence_tracks_specificity_and_trust(self) -> None:
        warning = build_validation_warning(
            {"scores": {"problem_solving_approach": 2}, "labels": {}, "feedback": {}, "reasoning": {}},
            {"anomaly_flags": ["misleading_metrics", "fake_metrics"], "contradiction_flags": ["metrics_contradiction"], "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.4, "tradeoffs": 0.4, "alternatives": 0.4}, "impact_strength": "moderate", "reasoning_depth": "implicit", "has_reasoning": False},
            {"metrics": ["metrics_contradiction"]},
        )
        influence = warning["validation"]["anomaly_influence"]
        self.assertTrue(influence["affects_score_confidence"])
        self.assertTrue(influence["affects_trust_level"])
        self.assertIn("specificity", influence["affected_dimensions"])
        self.assertIn("problem_solving_approach", influence["affected_dimensions"])
        self.assertEqual(influence["impact"], "major")
        self.assertIn("Misleading metrics weaken specificity confidence.", influence["reasons"])

    def test_low_trust_pass_is_marked_low_confidence(self) -> None:
        detail = build_overall_decision_detail({"relevance": 8, "structure": 8, "specificity": 8, "communication": 8, "problem_solving_approach": 8}, trust_level="low", score_confidence=0.9)
        self.assertEqual(detail["value"], "pass")
        self.assertEqual(detail["score_based_value"], "pass")
        self.assertEqual(detail["decision_confidence"], "low")
        self.assertFalse(detail["gating_applied"])
        self.assertIn("review", detail["reason"])

    def test_normalisation_disabled_by_default(self) -> None:
        normalisation = build_normalisation_detail({"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7})
        self.assertFalse(normalisation["enabled"])
        self.assertIsNone(normalisation["normalised_average"])
        self.assertEqual(normalisation["note"], "Normalisation disabled by default")

    def test_grounding_overrides_model_trust_with_evidence_context(self) -> None:
        result = ground_evaluation_result(
            {
                "scores": {"relevance": 8, "structure": 8, "specificity": 8, "communication": 8, "problem_solving_approach": 5},
                "labels": {},
                "feedback": {"summary": "", "strengths": [], "key_issues": [], "improvements": []},
                "reasoning": {},
                "follow_up": {},
                "trust": {"trust_level": "high", "trust_definition": "Model supplied", "score_confidence": 0.95, "decision_confidence": "high", "impact_strength": "strong", "reason": "Model supplied"},
                "validation_warning": {"trust_level": "high", "trust_definition": "Model supplied", "score_confidence": 0.95, "reasoning_depth": "deep", "interpretation": "Model supplied", "trust": {"trust_level": "high", "impact_strength": "strong"}},
            },
            {"has_metrics": True, "metric_count": 1, "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": ["misleading_metrics"], "impact_strength": "moderate", "evaluation_version": "trust-v4", "evaluation_trace": ["version:trust-v4"]},
        )
        self.assertEqual(result["trust"]["trust_level"], result["validation_warning"]["trust_level"])
        self.assertTrue(result["grounding_validation"]["enforced"])
        self.assertEqual(result["grounding_validation"]["source_of_truth"], "evaluation_context")

    def test_evaluate_answer_exposes_legacy_and_structured_decisions(self) -> None:
        with patch("interview_app_backend.services.evaluation_service.extract_evidence_context", return_value={"evaluation_version": "trust-v4", "evaluation_trace": ["version:trust-v4"], "has_metrics": True, "metric_count": 2, "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["90%"], "impact_strength": "strong"}), patch("interview_app_backend.services.evaluation_service.get_openrouter_client"), patch("interview_app_backend.services.evaluation_service.call_llm", return_value='{"evidence":{"metrics":["90%"],"actions":["cached work"],"reasoning":"Because it reduced risk"},"scores":{"technical_accuracy":8,"clarity":8,"structure":8,"relevance":8,"problem_solving_approach":8},"strengths":["Clear answer"],"improvement_areas":["Add detail"],"overall_summary":"Strong."}'), patch("interview_app_backend.services.evaluation_service.parse_json_response", return_value={"evidence": {"metrics": ["90%"], "actions": ["cached work"], "reasoning": "Because it reduced risk"}, "scores": {"technical_accuracy": 8, "clarity": 8, "structure": 8, "relevance": 8, "problem_solving_approach": 8, "specificity": 8, "communication": 8}, "labels": {}, "feedback": {"summary": "Strong.", "strengths": ["Clear answer"], "key_issues": [], "improvements": ["Add detail"]}, "reasoning": {"clarity": "", "alternative_approaches": "", "trade_off_awareness": "", "evidence": "Because it reduced risk"}, "follow_up": {"question": "", "type": "", "target_dimension": ""}, "example_answer": {}, "strengths": ["Clear answer"], "improvement_areas": ["Add detail"], "overall_summary": "Strong."}):
            result = evaluate_answer("Question?", "Answer.")
        self.assertEqual(result["overall_decision"], derive_overall_decision(result["scores"]))
        self.assertIn("overall_decision_detail", result)
        self.assertIn("normalisation", result)
        self.assertIn("normalised_score_detail", result)
        self.assertIsNone(result["normalised_score_detail"])
        self.assertEqual(result["overall_decision_detail"]["value"], result["overall_decision"])


if __name__ == "__main__":
    unittest.main()

import unittest

from pydantic import ValidationError

from interview_app_backend.llm.parser import parse_evidence_response, parse_json_response
from interview_app_backend.services.evaluation_rules import build_evaluation_context, validate_evaluation_consistency


class TestEvaluationParser(unittest.TestCase):
    def test_parse_json_response_returns_normalised_evaluation(self):
        payload = (
            '{"evidence":{"metrics":["90%"],"actions":["cached repeated work"],"reasoning":"Chose the simpler fix to reduce risk"},'
            '"scores":{"technical_accuracy":9,"clarity":8,"structure":7,"relevance":6,"problem_solving_approach":5},'
            '"strengths":["Clear answer"],"improvement_areas":["Add examples"],"overall_summary":"Strong response."}'
        )

        result = parse_json_response(payload)

        self.assertEqual(
            result,
            {
                "evidence": {
                    "metrics": ["90%"],
                    "actions": ["cached repeated work"],
                    "reasoning": "Chose the simpler fix to reduce risk",
                },
                "scores": {
                    "technical_accuracy": 9,
                    "clarity": 8,
                    "structure": 7,
                    "relevance": 6,
                    "problem_solving_approach": 5,
                    "specificity": 9,
                    "communication": 8,
                },
                "labels": {"relevance": "", "structure": "", "specificity": "", "communication": "", "problem_solving_approach": ""},
                "feedback": {"summary": "Strong response.", "strengths": ["Clear answer"], "key_issues": [], "improvements": ["Add examples"]},
                "reasoning": {"clarity": "", "alternative_approaches": "", "trade_off_awareness": "", "evidence": "Chose the simpler fix to reduce risk"},
                "follow_up": {"question": "", "type": "", "target_dimension": ""},
                "example_answer": {},
                "strengths": ["Clear answer"],
                "improvement_areas": ["Add examples"],
                "overall_summary": "Strong response.",
                "evaluation_version": "",
                "evaluation_trace": [],
                "impact_strength": "",
            },
        )

    def test_parse_json_response_rejects_missing_dimensions(self):
        with self.assertRaises(ValidationError):
            parse_json_response('{"scores":{"relevance":9}}')

    def test_parse_evidence_response_returns_structured_context(self):
        payload = (
            '{"has_metrics":true,"metrics":[{"type":"latency","before":"400ms","after":"90ms","change":"-78%"}],'
            '"has_structure":true,"has_reasoning":true,"has_tradeoffs":true,"has_alternatives":false,'
            '"confidence":{"metrics":0.9,"structure":0.8,"reasoning":0.7,"tradeoffs":0.6,"alternatives":0.5},'
            '"anomaly_flags":["fake_metrics"],"contradiction_flags":["metrics_contradiction"],"numeric_signals":["400ms","90ms"]}'
        )

        result = parse_evidence_response(payload)

        self.assertTrue(result["has_metrics"])
        self.assertEqual(result["metrics"][0]["type"], "latency")
        self.assertEqual(result["metrics"][0]["before"], "400ms")
        self.assertTrue(result["has_structure"])
        self.assertTrue(result["has_reasoning"])
        self.assertTrue(result["has_tradeoffs"])
        self.assertFalse(result["has_alternatives"])
        self.assertGreater(result["confidence"]["metrics"], 0.0)
        self.assertIn("fake_metrics", result["anomaly_flags"])
        self.assertIn("metrics_contradiction", result["contradiction_flags"])

    def test_build_evaluation_context_uses_fallback_numeric_detection(self):
        answer = "In 2024, I worked on v2 with 5 engineers and reduced latency from 400ms to 90ms."
        context = build_evaluation_context(
            {
                "has_metrics": False,
                "metrics": [],
                "has_structure": True,
                "has_reasoning": True,
                "has_tradeoffs": False,
                "has_alternatives": False,
            },
            answer=answer,
        )

        self.assertTrue(context["has_metrics"])
        self.assertEqual(context["metric_count"], 2)
        self.assertEqual(context["evaluation_version"], "trust-v4")
        self.assertIn("version:trust-v4", context["evaluation_trace"][0])
        self.assertIn("metrics_contradiction", context["contradiction_flags"])
        self.assertIn("non_impact_numbers", context["anomaly_flags"])
        self.assertEqual(context["impact_strength"], "strong")
        self.assertGreater(context["confidence"]["metrics"], 0.0)

    def test_parse_json_response_accepts_prompt_contract(self):
        payload = (
            '{"evaluation":{"overall_decision":"fail","scores":{"relevance":1,"structure":0,"specificity":0,"communication":0,"problem_solving_approach":1},'
            '"labels":{"relevance":"Off topic","structure":"","specificity":"","communication":"","problem_solving_approach":"Not demonstrated"}},'
            '"summary":"Not provided in the answer.","key_issues":["The answer is not relevant to the question."],"improvements":["Answer the question directly."],'
            '"reasoning":{"clarity":"Not provided in the answer","alternative_approaches":"Not provided in the answer","trade_off_awareness":"Not provided in the answer","evidence":"Not provided in the answer"},'
            '"follow_up":{"question":"Please answer the question directly.","type":"correction","target_dimension":"relevance"},'
            '"topic_match":false,"relevance_gate_applied":true,'
            '"trust":{"trust_level":"low","trust_definition":"Low confidence.","score_confidence":0.1,"decision_confidence":"high","impact_strength":"weak","reason":"Not relevant"}}'
        )

        result = parse_json_response(payload)

        self.assertEqual(result["overall_decision"], "fail")
        self.assertFalse(result["topic_match"])
        self.assertTrue(result["relevance_gate_applied"])
        self.assertEqual(result["evaluation"]["overall_decision"], "fail")
        self.assertEqual(result["feedback"]["summary"], "Not provided in the answer.")
        self.assertEqual(result["trust"]["trust_level"], "low")
        self.assertEqual(result["validation_warning"]["trust_level"], "low")
        self.assertEqual(result["overall_decision_detail"]["decision_confidence"], "high")

    def test_build_evaluation_context_flags_fake_metrics(self):
        context = build_evaluation_context(
            {
                "has_metrics": False,
                "metrics": [],
                "has_structure": False,
                "has_reasoning": False,
                "has_tradeoffs": False,
                "has_alternatives": False,
            },
            answer="I made the system 1000% better without changing the implementation.",
        )

        self.assertIn("fake_metrics", context["anomaly_flags"])

    def test_build_evaluation_context_flags_ambiguous_metrics(self):
        context = build_evaluation_context(
            {
                "has_metrics": False,
                "metrics": [],
                "has_structure": False,
                "has_reasoning": False,
                "has_tradeoffs": False,
                "has_alternatives": False,
            },
            answer="I handled 12 items during the project.",
        )

        self.assertIn("ambiguous_metrics", context["anomaly_flags"])

    def test_build_evaluation_context_flags_misleading_metrics(self):
        context = build_evaluation_context(
            {
                "has_metrics": False,
                "metrics": [],
                "has_structure": False,
                "has_reasoning": False,
                "has_tradeoffs": False,
                "has_alternatives": False,
            },
            answer="Latency improved by -20% after the change.",
        )

        self.assertIn("misleading_metrics", context["anomaly_flags"])
        self.assertIn("directional", context["grouped_anomaly_flags"])

    def test_parse_evidence_response_accepts_phrased_metrics(self):
        payload = (
            '{"has_metrics":true,"metrics":[{"type":"latency","before":"","after":"under 100 milliseconds","change":"roughly 4x faster"}],'
            '"has_structure":false,"has_reasoning":true,"has_tradeoffs":false,"has_alternatives":false}'
        )

        result = parse_evidence_response(payload)

        self.assertEqual(result["metrics"][0]["after"], "under 100 milliseconds")
        self.assertEqual(result["metrics"][0]["change"], "roughly 4x faster")
        self.assertTrue(result["has_metrics"])
        self.assertTrue(result["has_reasoning"])

    def test_validate_evaluation_consistency_normalises_metric_contradictions(self):
        evaluation = {
            "labels": {"specificity": "Lacks measurable outcomes", "structure": "Lacks structure"},
            "feedback": {
                "key_issues": [
                    "Missing specific metrics for improvement",
                    "Reasoning is implicit",
                    "No alternatives considered",
                ],
                "improvements": [
                    "Add quantifiable results such as latency reduction or throughput gains",
                    "Explain technical decisions and trade-offs",
                    "Discuss alternative approaches and why they were rejected",
                ],
            },
            "reasoning": {
                "clarity": "",
                "alternative_approaches": "No alternatives considered",
                "trade_off_awareness": "Trade-offs are missing",
                "evidence": "Reasoning is implicit",
            },
            "scores": {"problem_solving_approach": 3},
        }
        context = {
            "has_metrics": True,
            "has_structure": True,
            "has_reasoning": True,
            "has_tradeoffs": True,
            "has_alternatives": True,
            "contradiction_flags": ["metrics_contradiction"],
            "anomaly_flags": ["ambiguous_metrics", "misleading_metrics"],
            "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.6, "alternatives": 0.5},
            "impact_strength": "moderate",
        }

        with self.assertLogs("interview_app_backend.services.evaluation_rules", level="WARNING") as captured:
            result = validate_evaluation_consistency(evaluation, context)

        self.assertEqual(result["labels"]["specificity"], "Metrics are present, but could be tied more clearly to business or user impact.")
        self.assertEqual(result["labels"]["structure"], "Clear sections are present, but STAR alignment could be stronger.")
        self.assertIn("decision-making behind each technical choice", result["feedback"]["key_issues"][0])
        self.assertIn("Keep the existing metrics", result["feedback"]["improvements"][0])
        self.assertIn("metrics_contradiction", result["contradiction_flags"])
        self.assertTrue(result["validation_warning"]["has_warning"])
        self.assertEqual(result["validation_warning"]["severity"], "high")
        self.assertEqual(result["validation_warning"]["trust_level"], "low")
        self.assertIn("Material contradiction", result["validation_warning"]["severity_definition"])
        self.assertEqual(result["reasoning_depth"], "developing")
        self.assertIn("validation", result["validation_warning"])
        self.assertIn("reasoning", result["validation_warning"])
        self.assertEqual(result["validation_warning"]["validation"]["impact_strength"], "moderate")
        self.assertIn("reasoning", result["validation_warning"]["dimension_contradictions"])
        self.assertIn("tradeoffs", result["validation_warning"]["dimension_contradictions"])
        self.assertIn("alternatives", result["validation_warning"]["dimension_contradictions"])
        self.assertIn("ambiguous_metrics", result["validation_warning"]["anomaly_flags"])
        self.assertIn("grouped_anomaly_flags", result["validation_warning"])
        self.assertGreaterEqual(result["score_confidence"], 0)
        self.assertTrue(result["validation_warnings"])
        self.assertTrue(any("normalised" in line.lower() for line in captured.output))


if __name__ == "__main__":
    unittest.main()

import unittest

from pydantic import ValidationError

from interview_app_backend.llm.parser import parse_json_response


class TestEvaluationParserRepair(unittest.TestCase):
    def test_parse_json_response_repairs_and_clamps_scores(self):
        payload = (
            '```json\n{"evidence":{"metrics":[],"actions":[],"reasoning":""},'
            '"scores":{"technical_accuracy":9.6,"clarity":12,"structure":-1,"relevance":8,"problem_solving_approach":7.2,"specificity":6,"communication":5},'
            '"labels":{"relevance":"","structure":"","specificity":"","communication":"","problem_solving_approach":""},'
            '"feedback":{"summary":"","strengths":[],"key_issues":[],"improvements":[]},'
            '"reasoning":{"clarity":"","alternative_approaches":"","trade_off_awareness":"","evidence":""},'
            '"follow_up":{"question":"","type":"","target_dimension":""},'
            '"example_answer":{},"strengths":[],"improvement_areas":[],"overall_summary":""}\n```'
        )

        with self.assertLogs("interview_app_backend.llm.parser", level="INFO") as captured:
            result = parse_json_response(payload)

        self.assertEqual(result["scores"]["technical_accuracy"], 10)
        self.assertEqual(result["scores"]["clarity"], 10)
        self.assertEqual(result["scores"]["structure"], 0)
        self.assertEqual(result["scores"]["relevance"], 8)
        self.assertEqual(result["scores"]["problem_solving_approach"], 7)
        self.assertTrue(any("validation=repaired" in line for line in captured.output))

    def test_parse_json_response_rejects_non_numeric_score(self):
        payload = (
            '{"evidence":{"metrics":[],"actions":[],"reasoning":""},'
            '"scores":{"technical_accuracy":9,"clarity":"high","structure":7,"relevance":6,"problem_solving_approach":5,"specificity":9,"communication":8},'
            '"labels":{"relevance":"","structure":"","specificity":"","communication":"","problem_solving_approach":""},'
            '"feedback":{"summary":"","strengths":[],"key_issues":[],"improvements":[]},'
            '"reasoning":{"clarity":"","alternative_approaches":"","trade_off_awareness":"","evidence":""},'
            '"follow_up":{"question":"","type":"","target_dimension":""},'
            '"example_answer":{},"strengths":[],"improvement_areas":[],"overall_summary":""}'
        )

        with self.assertRaises(ValidationError):
            parse_json_response(payload)


if __name__ == "__main__":
    unittest.main()

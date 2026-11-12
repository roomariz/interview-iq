import unittest

from interview_app_backend.services.gap_analysis_service import analyse_gaps


class TestGapAnalysis(unittest.TestCase):

    def test_analyse_gaps_returns_empty_structure_for_empty_inputs(self):
        result = analyse_gaps("", "")
        self.assertIn("has_gaps", result)

    def test_analyse_gaps_detects_matching_skills(self):
        cv = "Skills: Python, Java, AWS"
        jd = "Required: Python, Java"
        result = analyse_gaps(cv, jd)
        self.assertIn("python", result.get("matching_skills", []))
        self.assertIn("java", result.get("matching_skills", []))

    def test_analyse_gaps_detects_missing_skills(self):
        cv = "Skills: Python"
        jd = "Required: Python, Java, AWS"
        result = analyse_gaps(cv, jd)
        self.assertIn("java", result.get("missing_skills", []))
        self.assertIn("aws", result.get("missing_skills", []))

    def test_analyse_gaps_no_gaps_when_all_matched(self):
        cv = "Skills: Python, Java, AWS"
        jd = "Required: Python"
        result = analyse_gaps(cv, jd)
        self.assertFalse(result.get("has_gaps"))

    def test_analyse_gaps_has_gaps_when_some_missing(self):
        cv = "Skills: Python"
        jd = "Required: Python, Java"
        result = analyse_gaps(cv, jd)
        self.assertTrue(result.get("has_gaps"))

    def test_analyse_gaps_calculates_experience_gap(self):
        cv = "7 years experience"
        jd = "5 years experience required"
        result = analyse_gaps(cv, jd)
        self.assertEqual(result.get("experience_gap"), 2)

    def test_analyse_gaps_experience_gap_negative(self):
        cv = "2 years experience"
        jd = "5 years experience required"
        result = analyse_gaps(cv, jd)
        self.assertEqual(result.get("experience_gap"), -3)

    def test_analyse_gaps_builds_gap_summary(self):
        cv = "Skills: Python"
        jd = "Required: Python, Java, AWS, Docker"
        result = analyse_gaps(cv, jd)
        summary = result.get("gap_summary", "")
        self.assertIn("Missing", summary)

    def test_analyse_gaps_no_gap_summary_when_all_matched(self):
        cv = "Skills: Python, Java"
        jd = "Required: Python, Java"
        result = analyse_gaps(cv, jd)
        self.assertEqual(result.get("gap_summary"), "All required skills matched.")


if __name__ == "__main__":
    unittest.main()
import json
import unittest

from interview_app_backend.services.report_service import build_report


class TestReportService(unittest.TestCase):
    def test_build_report_returns_downloadable_json_report(self):
        session_summary = {
            "overall_summary": "Strong performance.",
            "scores": {"technical_accuracy": 8, "clarity": 7},
            "strengths": ["Explained decisions clearly"],
            "improvement_areas": ["Add more metrics"],
        }

        report = build_report(session_summary)

        self.assertEqual(report.title, "Interview Session Report")
        self.assertEqual(report.filename, "interview-session-report.json")
        self.assertEqual(report.mime_type, "application/json")
        self.assertEqual(report.sections, ["summary", "scores", "strengths", "improvement_areas"])
        self.assertEqual(json.loads(report.content), session_summary)


if __name__ == "__main__":
    unittest.main()

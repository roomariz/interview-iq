import unittest

from interview_app_backend.cv.job_description import parse_job_description


class TestJobDescriptionParsing(unittest.TestCase):

    def test_parse_jd_returns_empty_for_empty_text(self):
        result = parse_job_description("")
        self.assertEqual(result, {})

    def test_parse_jd_returns_empty_for_whitespace_only(self):
        result = parse_job_description("   \n\t  ")
        self.assertEqual(result, {})

    def test_parse_jd_extracts_role_title(self):
        jd = "Senior Backend Engineer\nWe are looking for a talented engineer"
        result = parse_job_description(jd)
        self.assertIn("role_title", result)

    def test_parse_jd_extracts_required_skills(self):
        jd = "Required skills: Python, Java, AWS, Docker"
        result = parse_job_description(jd)
        skills = result.get("required_skills", [])
        self.assertIn("python", skills)
        self.assertIn("aws", skills)

    def test_parse_jd_extracts_experience_years(self):
        jd = "Minimum 5 years of experience required"
        result = parse_job_description(jd)
        self.assertEqual(result.get("required_experience"), 5)

    def test_parse_jd_extracts_experience_with_plus(self):
        jd = "3+ years in software development"
        result = parse_job_description(jd)
        self.assertEqual(result.get("required_experience"), 3)

    def test_parse_jd_extracts_location(self):
        jd = "Location: San Francisco, CA"
        result = parse_job_description(jd)
        self.assertIn("location", result)

    def test_parse_jd_extracts_remote(self):
        jd = "This is a remote position"
        result = parse_job_description(jd)
        self.assertIn("location", result)

    def test_parse_jd_extracts_employment_type(self):
        jd = "Employment type: full-time"
        result = parse_job_description(jd)
        self.assertEqual(result.get("employment_type"), "full-time")

    def test_parse_jd_extracts_full_structure(self):
        jd = """Senior Backend Engineer

Required skills: Python, Go, PostgreSQL, AWS
5+ years experience
Remote
Full-time
"""
        result = parse_job_description(jd)
        self.assertIn("role_title", result)
        self.assertIn("required_skills", result)
        self.assertIn("required_experience", result)
        self.assertEqual(result.get("employment_type"), "full-time")

    def test_parse_jd_handles_realistic_jd(self):
        jd = """Backend Engineer (Python)

We are looking for a Backend Engineer to join our team.

Requirements:
- 4+ years of backend development experience
- Strong Python skills
- Experience with AWS and Docker
- SQL and NoSQL databases

This is a hybrid role based in New York.
"""
        result = parse_job_description(jd)
        self.assertIn("python", result.get("required_skills", []))
        self.assertEqual(result.get("required_experience"), 4)


if __name__ == "__main__":
    unittest.main()
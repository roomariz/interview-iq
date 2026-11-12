import unittest

from interview_app_backend.cv.parser import parse_cv


class TestCvParsing(unittest.TestCase):

    def test_parse_cv_returns_empty_for_empty_text(self):
        result = parse_cv("")
        self.assertEqual(result, {})

    def test_parse_cv_returns_empty_for_whitespace_only(self):
        result = parse_cv("   \n\t  ")
        self.assertEqual(result, {})

    def test_parse_cv_extracts_name(self):
        cv = "John Doe\nSoftware Engineer\njohn@example.com"
        result = parse_cv(cv)
        self.assertIn("name", result)

    def test_parse_cv_extracts_email(self):
        cv = "John Doe\njohn.doe@example.com\nSoftware Engineer"
        result = parse_cv(cv)
        self.assertEqual(result.get("email"), "john.doe@example.com")

    def test_parse_cv_extracts_email_complex(self):
        cv = "Contact: user.name+tag@sub.domain.co.uk"
        result = parse_cv(cv)
        self.assertEqual(result.get("email"), "user.name+tag@sub.domain.co.uk")

    def test_parse_cv_extracts_phone(self):
        cv = "John Doe\n+1 555-123-4567\nSoftware Engineer"
        result = parse_cv(cv)
        self.assertIn("phone", result)

    def test_parse_cv_extracts_python_skill(self):
        cv = "Skills: Python, Java, Docker"
        result = parse_cv(cv)
        skills = result.get("skills", [])
        self.assertIn("python", skills)

    def test_parse_cv_extracts_multiple_skills(self):
        cv = "Experience with Python, Java, React, AWS, Docker and Kubernetes"
        result = parse_cv(cv)
        skills = result.get("skills", [])
        self.assertIn("python", skills)
        self.assertIn("java", skills)
        self.assertIn("react", skills)
        self.assertIn("aws", skills)

    def test_parse_cv_extracts_experience_years(self):
        cv = "5 years of experience in software development"
        result = parse_cv(cv)
        self.assertEqual(result.get("experience_years"), 5)

    def test_parse_cv_extracts_experience_variants(self):
        cv = "8+ years experience"
        result = parse_cv(cv)
        self.assertEqual(result.get("experience_years"), 8)

    def test_parse_cv_limits_experience_to_realistic_range(self):
        cv = "99 years experience"
        result = parse_cv(cv)
        self.assertEqual(result.get("experience_years"), 0)

    def test_parse_cv_extracts_roles(self):
        cv = "Senior Software Engineer\nBackend Developer\nTech Lead"
        result = parse_cv(cv)
        roles = result.get("roles", [])
        self.assertGreater(len(roles), 0)

    def test_parse_cv_extracts_education(self):
        cv = "Bachelor of Science in Computer Science\nUniversity of Tech\nMasters in AI"
        result = parse_cv(cv)
        education = result.get("education", [])
        self.assertGreater(len(education), 0)

    def test_parse_cv_returns_full_structure(self):
        cv = """John Doe
john@example.com
+1 555-123-4567

Senior Software Engineer

Skills: Python, Java, AWS, Docker

5 years experience

BSC Computer Science - Tech University
"""
        result = parse_cv(cv)
        self.assertIn("name", result)
        self.assertIn("email", result)
        self.assertIn("skills", result)
        self.assertIn("experience_years", result)
        self.assertIn("roles", result)
        self.assertIn("education", result)

    def test_parse_cv_handles_realistic_cv(self):
        cv = """Michael Chen
michael.chen@email.com
+1 415-555-7890

Senior Backend Engineer at TechCorp

Skills: Python, Go, PostgreSQL, Redis, AWS, Kubernetes
7 years of backend development experience

Masters in Computer Science - Stanford University
"""
        result = parse_cv(cv)
        self.assertEqual(result.get("email"), "michael.chen@email.com")
        self.assertIn("python", result.get("skills", []))
        self.assertEqual(result.get("experience_years"), 7)


if __name__ == "__main__":
    unittest.main()
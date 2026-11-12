import re


def parse_job_description(text: str) -> dict:
    if not text or not text.strip():
        return {}

    text = text.strip()

    required_skills = _extract_skills(text)
    required_experience = _extract_experience(text)
    role_title = _extract_role_title(text)
    location = _extract_location(text)
    employment_type = _extract_employment_type(text)

    return {
        "role_title": role_title,
        "required_skills": required_skills,
        "required_experience": required_experience,
        "location": location,
        "employment_type": employment_type,
    }


def _extract_role_title(text: str) -> str:
    lines = text.split("\n")
    for line in lines[:10]:
        clean = line.strip()
        if len(clean) > 0 and len(clean) < 80:
            if _looks_like_role_title(clean):
                return clean
    return ""


def _looks_like_role_title(line: str) -> bool:
    role_words = ["engineer", "developer", "manager", "lead", "architect", "analyst", "specialist", "designer", "consultant"]
    line_lower = line.lower()
    for word in role_words:
        if word in line_lower:
            return True
    return False


def _extract_skills(text: str) -> list:
    skill_keywords = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "react", "angular", "vue", "node", "django", "fastapi", "flask",
        "git", "linux", "bash", "shell", "ci/cd", "jenkins", "github actions",
        "machine learning", "data science", "nlp", "deep learning", "tensorflow", "pytorch",
        "api", "rest", "graphql", "microservices", "distributed systems",
        "agile", "scrum", "jira", "confluence", "spark", "hadoop", "kafka",
    ]

    found = []
    text_lower = text.lower()
    for skill in skill_keywords:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def _extract_experience(text: str) -> int:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
        r"experience[:\s]*(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\s*years?\s*(?:in|of|required|minimum)",
        r"(\d+)\+\s*years",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            if 0 < years < 50:
                return years
    return 0


def _extract_location(text: str) -> str:
    location_patterns = [
        r"(?:location|located|remote|hybrid|on-site)[:\s]*([a-zA-Z\s,]+)",
        r"(remote|hybrid|on-site|office)",
    ]

    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.group(1) else match.group(0)
    return ""


def _extract_employment_type(text: str) -> str:
    type_keywords = [
        ("full-time", "full-time"),
        ("part-time", "part-time"),
        ("contract", "contract"),
        ("freelance", "freelance"),
        ("permanent", "permanent"),
    ]

    text_lower = text.lower()
    for keyword, employment_type in type_keywords:
        if keyword in text_lower:
            return employment_type
    return ""
import re


def parse_cv(text: str) -> dict:
    if not text or not text.strip():
        return {}

    text = text.strip()

    name = _extract_name(text)
    email = _extract_email(text)
    phone = _extract_phone(text)
    skills = _extract_skills(text)
    experience_years = _extract_experience(text)
    roles = _extract_roles(text)
    education = _extract_education(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience_years": experience_years,
        "roles": roles,
        "education": education,
    }


def _extract_name(text: str) -> str:
    lines = text.split("\n")
    for line in lines[:5]:
        clean = line.strip()
        if len(clean) > 0 and len(clean) < 50:
            if not _looks_like_contact(clean):
                return clean
    return ""


def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"\+?[\d\s\-\(\)]{10,}", text)
    return match.group(0).strip() if match else ""


def _extract_skills(text: str) -> list:
    skill_keywords = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "react", "angular", "vue", "node", "django", "fastapi", "flask",
        "git", "linux", "bash", "shell", "ci/cd", "jenkins", "github actions",
        "machine learning", "data science", "nlp", "deep learning", "tensorflow", "pytorch",
        "api", "rest", "graphql", "microservices", "distributed systems",
        "agile", "scrum", "jira", "confluence",
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
        r"(\d+)\s*years?\s*(?:in|of|total)",
        r"(\d+)\+\s*years?\s*experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            if 0 < years < 50:
                return years
    return 0


def _extract_roles(text: str) -> list:
    role_keywords = [
        "engineer", "developer", "manager", "lead", "architect", "analyst",
        "designer", "consultant", "specialist", "coordinator", "director",
    ]

    roles = []
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower()
        for role in role_keywords:
            if role in line_lower:
                clean = line.strip()
                if clean and len(clean) < 80:
                    roles.append(clean)
                break
    return roles[:5]


def _extract_education(text: str) -> list:
    education_keywords = ["university", "college", "bachelor", "master", "phd", "degree", "bsc", "msc", "b.tech", "m.tech"]

    edu = []
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower()
        for keyword in education_keywords:
            if keyword in line_lower:
                clean = line.strip()
                if clean and len(clean) < 100:
                    edu.append(clean)
                break
    return edu[:3]


def _looks_like_contact(line: str) -> bool:
    contact_patterns = [
        r"@",
        r"^[\d\-\(\)\+]+$",
        r"^(email|phone|mobile|linkedin|github|http)",
    ]
    line_lower = line.lower()
    for pattern in contact_patterns:
        if re.search(pattern, line_lower):
            return True
    return False
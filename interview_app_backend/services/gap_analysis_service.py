from interview_app_backend.cv.parser import parse_cv
from interview_app_backend.cv.job_description import parse_job_description


def analyse_gaps(cv_text: str, job_description_text: str) -> dict:
    cv_profile = parse_cv(cv_text)
    jd_profile = parse_job_description(job_description_text)

    if not cv_profile and not jd_profile:
        return {
            "has_gaps": False,
            "missing_skills": [],
            "matching_skills": [],
            "gap_summary": "",
        }

    cv_skills = set(cv_profile.get("skills", []))
    jd_skills = set(jd_profile.get("required_skills", []))

    matching_skills = cv_skills.intersection(jd_skills)
    missing_skills = jd_skills - cv_skills

    has_gaps = len(missing_skills) > 0

    gap_summary = _build_gap_summary(matching_skills, missing_skills, jd_profile)

    return {
        "has_gaps": has_gaps,
        "missing_skills": list(missing_skills),
        "matching_skills": list(matching_skills),
        "gap_summary": gap_summary,
        "cv_experience": cv_profile.get("experience_years", 0),
        "jd_experience": jd_profile.get("required_experience", 0),
        "experience_gap": _calculate_experience_gap(cv_profile, jd_profile),
    }


def _build_gap_summary(matching_skills: set, missing_skills: set, jd_profile: dict) -> str:
    if not missing_skills:
        return "All required skills matched."

    missing_list = sorted(list(missing_skills))
    if len(missing_list) <= 3:
        missing_str = ", ".join(missing_list)
    else:
        missing_str = f"{', '.join(missing_list[:3])} and {len(missing_list) - 3} more"

    return f"Missing: {missing_str}"


def _calculate_experience_gap(cv_profile: dict, jd_profile: dict) -> int:
    cv_exp = cv_profile.get("experience_years", 0)
    jd_exp = jd_profile.get("required_experience", 0)

    if jd_exp == 0:
        return 0

    return cv_exp - jd_exp
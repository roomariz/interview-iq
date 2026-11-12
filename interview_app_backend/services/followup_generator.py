from typing import Optional
from interview_app_backend.services.gap_analysis_service import analyse_gaps
from interview_app_backend.services.question_distribution import QuestionType, get_question_type_prompt


def generate_adaptive_followup(
    previous_question: str,
    previous_answer: str,
    cv_text: str,
    job_description_text: str,
    feedback_score: Optional[int] = None,
) -> str:
    gap_analysis = analyse_gaps(cv_text, job_description_text)

    if feedback_score is not None and feedback_score < 5:
        focus_area = "weakness"
    elif gap_analysis.get("has_gaps"):
        focus_area = "gap"
    else:
        focus_area = "depth"

    return _build_followup_prompt(previous_question, previous_answer, focus_area, gap_analysis)


def _build_followup_prompt(previous_question: str, previous_answer: str, focus_area: str, gap_analysis: dict) -> str:
    missing_skills = gap_analysis.get("missing_skills", [])

    if focus_area == "gap" and missing_skills:
        skill_context = f"Focus on: {', '.join(missing_skills[:2])}"
    else:
        skill_context = ""

    prompt = f"""Ask a follow-up question based on this Q&A:

Previous question: {previous_question}
Previous answer: {previous_answer}
{focus_area.capitalize()}: {skill_context}

Return one clarifying follow-up question only.
"""
    return prompt.strip()


def get_followup_context_from_gaps(gap_analysis: dict) -> str:
    missing_skills = gap_analysis.get("missing_skills", [])
    if not missing_skills:
        return ""

    return f"Address skill gaps: {', '.join(missing_skills[:3])}"


def should_ask_followup(answer_quality_score: Optional[int] = None, has_gaps: bool = False) -> bool:
    if answer_quality_score is not None and answer_quality_score < 4:
        return True

    if has_gaps:
        return True

    return False
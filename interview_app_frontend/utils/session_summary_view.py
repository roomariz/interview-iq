from collections.abc import Mapping
from typing import Any

REQUIRED_DIMENSIONS = frozenset(("relevance", "structure", "specificity", "communication", "problem_solving_approach"))


def is_valid_answer(answer: Mapping[str, Any]) -> bool:
    scores = answer.get("scores")
    if scores is None or not isinstance(scores, dict) or not scores:
        return False
    return REQUIRED_DIMENSIONS.issubset(scores.keys())


def is_degraded_evaluation(answer: Mapping[str, Any]) -> bool:
    trust = answer.get("trust", {})
    if isinstance(trust, dict):
        trust_level = trust.get("trust_level", "high")
        if trust_level in ("low", "medium"):
            return True
    evaluation_confidence = answer.get("evaluation_confidence", {})
    if isinstance(evaluation_confidence, dict):
        overall = evaluation_confidence.get("overall", 1.0)
        if overall < 0.5:
            return True
    return False


def build_session_summary_view(session_state: Mapping[str, Any]) -> dict[str, Any]:
    summary = dict(session_state.get("summary", {}))
    latest_feedback = session_state.get("feedback")
    answers = session_state.get("answers", [])
    fallback_strengths = _extract_answer_notes(answers, "strengths")
    fallback_improvements = _extract_answer_notes(answers, "improvements", secondary_key="key_issues")
    fallback_focus_areas = _extract_answer_notes(answers, "focus_areas")
    latest_question_recap = _build_latest_question_recap(answers, latest_feedback)
    if not summary:
        scores = list(answers or [{}]) or []
        completed = len([answer for answer in scores if isinstance(answer, Mapping)])
        duration = session_state.get("session_duration_minutes", 0)
        strengths = _extract_strengths(latest_feedback) or fallback_strengths
        improvements = _extract_improvements(latest_feedback) or fallback_improvements
        focus_areas = _extract_focus_areas(session_state.get("focus_areas")) or fallback_focus_areas
        summary = _build_summary_from_raw(scores, completed, duration, strengths, improvements, focus_areas)
    merged = _merge_summary_with_feedback(summary, session_state, latest_feedback)
    if latest_question_recap:
        merged["latest_question_recap"] = latest_question_recap
    return merged


def _build_summary_from_raw(
    answers: list[Mapping[str, Any]], completed: int, duration: int, strengths: list[str], improvements: list[str], focus_areas: list[str]
) -> dict[str, Any]:
    valid_answers = []
    degraded_count = 0
    for ans in answers:
        if isinstance(ans, dict) and is_valid_answer(ans):
            valid_answers.append(ans)
            if is_degraded_evaluation(ans):
                degraded_count += 1

    if not valid_answers:
        return {
            "title": "Interview Session Complete!",
            "overall_performance": "0% (Needs Improvement)",
            "questions_completed": completed,
            "session_duration": f"{duration} minutes",
            "average_scores": {},
            "strengths": strengths,
            "improvement_areas": improvements,
            "focus_areas": focus_areas,
            "recommended_next_steps": [],
            "evaluation_notice": f"{completed} question(s) could not be evaluated.",
        }

    evaluated_successfully = len(valid_answers)
    evaluation_notice = ""
    if degraded_count > 0:
        if completed == 1 or evaluated_successfully == completed:
            evaluation_notice = f"{evaluated_successfully} question{'s' if evaluated_successfully != 1 else ''} evaluated with reduced confidence."
        else:
            evaluation_notice = f"{evaluated_successfully}/{completed} questions evaluated with reduced confidence."
    elif evaluated_successfully < completed:
        evaluation_notice = f"{evaluated_successfully}/{completed} questions evaluated successfully."

    all_scores = [ans.get("scores", {}) for ans in valid_answers]
    dimensions = ["relevance", "structure", "specificity", "communication", "problem_solving_approach"]
    avg_scores = {}
    for dim in dimensions:
        values = [s.get(dim, 0) for s in all_scores if dim in s]
        if values:
            avg_scores[dim] = round(sum(values) / len(values), 1)
    overall = round(sum(avg_scores.values()) / len(avg_scores), 1) if avg_scores else 0.0
    readiness = "Needs Improvement" if overall < 7 else "Good"
    return {
        "title": "Interview Session Complete!",
        "overall_performance": f"{int(round(overall * 10))}% ({readiness})",
        "questions_completed": completed,
        "session_duration": f"{duration} minutes",
        "average_scores": avg_scores,
        "strengths": strengths[:3],
        "improvement_areas": improvements[:4],
        "focus_areas": focus_areas[:4],
        "recommended_next_steps": [
            "Practice STAR framework (Situation, Task, Action, Result)",
            "Prepare specific metrics for key projects",
            "Practice follow-up questions on technical trade-offs",
        ],
        "evaluation_notice": evaluation_notice,
    }


def _extract_strengths(feedback) -> list[str]:
    if isinstance(feedback, dict):
        strengths = feedback.get("strengths", [])
        if isinstance(strengths, list):
            return [str(s) for s in strengths if s]
    return []


def _extract_improvements(feedback) -> list[str]:
    if isinstance(feedback, dict):
        improvements = feedback.get("improvements", [])
        if isinstance(improvements, list):
            return [str(i) for i in improvements if i]
        key_issues = feedback.get("key_issues", [])
        if isinstance(key_issues, list):
            return [str(i) for i in key_issues if i]
    return []


def _extract_answer_notes(answers, primary_key: str, secondary_key: str | None = None) -> list[str]:
    if not isinstance(answers, list):
        return []
    notes: list[str] = []
    for answer in answers:
        if not isinstance(answer, Mapping):
            continue
        items = answer.get(primary_key, [])
        if not isinstance(items, list) and secondary_key:
            items = answer.get(secondary_key, [])
        if isinstance(items, list):
            notes.extend(str(item) for item in items if str(item).strip())
    return notes


def _build_latest_question_recap(answers, latest_feedback) -> dict[str, Any]:
    if not isinstance(answers, list):
        return {}
    latest_answer = next((answer for answer in reversed(answers) if isinstance(answer, Mapping)), {})
    if not latest_answer:
        return {}
    feedback_strengths = _extract_strengths(latest_feedback)
    feedback_improvements = _extract_improvements(latest_feedback)
    return {
        "question": str(latest_answer.get("question", "")).strip(),
        "decision": str(latest_answer.get("overall_decision", "")).strip(),
        "summary": str(latest_answer.get("summary", "")).strip(),
        "strengths": (list(latest_answer.get("strengths", [])) if isinstance(latest_answer.get("strengths"), list) else []) or feedback_strengths,
        "improvement_areas": (list(latest_answer.get("improvements", [])) if isinstance(latest_answer.get("improvements"), list) else []) or feedback_improvements,
    }


def _extract_focus_areas(focus_areas) -> list[str]:
    if isinstance(focus_areas, list):
        return [str(item) for item in focus_areas if str(item).strip()]
    return []


def _normalise_session_summary(summary: dict[str, Any], session_state: Mapping[str, Any]) -> dict[str, Any]:
    title = str(summary.get("title", "Interview Session Complete!")).strip()
    performance = str(summary.get("overall_performance", "")).strip()
    if not performance:
        performance = "0% (Needs Improvement)"
    questions = summary.get("questions_completed", 0)
    duration = summary.get("session_duration", "0 minutes")
    avg_scores = dict(summary.get("average_scores", {})) if isinstance(summary.get("average_scores"), dict) else {}
    strengths = list(summary.get("strengths", [])) if isinstance(summary.get("strengths"), list) else []
    improvements = list(summary.get("improvement_areas", [])) if isinstance(summary.get("improvement_areas"), list) else []
    focus_areas = list(summary.get("focus_areas", [])) if isinstance(summary.get("focus_areas"), list) else []
    next_steps = list(summary.get("recommended_next_steps", [])) if isinstance(summary.get("recommended_next_steps"), list) else []
    evaluation_notice = str(summary.get("evaluation_notice", "")).strip()
    return {
        "title": title,
        "overall_performance": performance,
        "questions_completed": questions,
        "session_duration": duration,
        "average_scores": avg_scores,
        "strengths": strengths,
        "improvement_areas": improvements,
        "focus_areas": focus_areas,
        "recommended_next_steps": next_steps,
        "evaluation_notice": evaluation_notice,
    }


def _merge_summary_with_feedback(summary: dict[str, Any], session_state: Mapping[str, Any], latest_feedback: Any) -> dict[str, Any]:
    normalised = _normalise_session_summary(summary, session_state)
    answers = session_state.get("answers", [])
    fallback_strengths = _extract_strengths(latest_feedback) or _extract_answer_notes(answers, "strengths")
    fallback_improvements = _extract_improvements(latest_feedback) or _extract_answer_notes(answers, "improvements", secondary_key="key_issues")
    fallback_focus_areas = _extract_focus_areas(session_state.get("focus_areas")) or _extract_answer_notes(answers, "focus_areas")
    fallback_notice = ""

    answers = session_state.get("answers", [])
    if isinstance(answers, list):
        graded_answers = [answer for answer in answers if isinstance(answer, Mapping) and is_valid_answer(answer)]
        if graded_answers:
            degraded_count = len([answer for answer in graded_answers if is_degraded_evaluation(answer)])
            if degraded_count:
                completed = int(normalised.get("questions_completed", len(answers)) or len(answers))
                if completed == 1 or degraded_count == completed:
                    fallback_notice = f"{degraded_count} question{'s' if degraded_count != 1 else ''} evaluated with reduced confidence."
                else:
                    fallback_notice = f"{degraded_count}/{completed} questions evaluated with reduced confidence."

    if not normalised["strengths"] and fallback_strengths:
        normalised["strengths"] = fallback_strengths
    if not normalised["improvement_areas"] and fallback_improvements:
        normalised["improvement_areas"] = fallback_improvements
    if not normalised["focus_areas"] and fallback_focus_areas:
        normalised["focus_areas"] = fallback_focus_areas
    if not normalised["evaluation_notice"] and fallback_notice:
        normalised["evaluation_notice"] = fallback_notice
    return normalised

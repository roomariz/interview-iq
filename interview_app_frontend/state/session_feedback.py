from interview_app_frontend.state.session_helpers import _is_valid_evaluation_for_storage, _coerce_list, _update_adaptation_state
from interview_app_frontend.state.answer_evaluation_job import reset_answer_evaluation_state
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import build_follow_up, build_key_takeaway

def _apply_answer_feedback(state, question: str, answer: str, feedback: dict) -> None:
    import time as time_module

    if not _is_valid_evaluation_for_storage(feedback):
        state.answer_evaluation_notice = "Could not store this evaluation due to incomplete scores."
        return

    view_model = normalise_feedback_payload(feedback)
    trust = feedback.get("trust", {})
    evaluation_confidence = feedback.get("evaluation_confidence", {})
    state.answers = [
        *state.get("answers", []),
        {
            "question": question,
            "answer": answer,
            "scores": dict(view_model.get("scores", {})),
            "labels": dict(view_model.get("labels", {})) if isinstance(view_model.get("labels"), dict) else {},
            "overall_decision": str(view_model.get("overall_decision", "")).strip(),
            "summary": str(view_model.get("feedback", {}).get("summary", "")).strip() if isinstance(view_model.get("feedback"), dict) else "",
            "strengths": list(view_model.get("strengths", [])) if isinstance(view_model.get("strengths"), list) else [],
            "key_issues": list(view_model.get("key_issues", [])) if isinstance(view_model.get("key_issues"), list) else [],
            "improvements": list(view_model.get("improvements", [])) if isinstance(view_model.get("improvements"), list) else [],
            "trust": dict(trust) if isinstance(trust, dict) else {},
            "evaluation_confidence": dict(evaluation_confidence) if isinstance(evaluation_confidence, dict) else {},
        },
    ]
    state.reference_answer = feedback.get("reference_answer", "")
    state.semantic_similarity_score = feedback.get("semantic_similarity_score", 0.0)
    state.feedback = feedback
    follow_up = build_follow_up(view_model)
    takeaway = build_key_takeaway(view_model)
    _update_adaptation_state(state, view_model.get("scores", {}), _coerce_list(state.get("competencies", [])))
    memory_entry = {
        "question": view_model["question"],
        "takeaway": takeaway,
        "follow_up_question": follow_up.get("question", ""),
        "follow_up_stage": follow_up.get("stage", 1),
        "focus": follow_up.get("target_dimension", "problem_solving_approach"),
    }
    state.follow_up_questions = [*state.get("follow_up_questions", []), follow_up]
    relevance_score = int(view_model.get("scores", {}).get("relevance", 0))
    memory_allowed = bool(view_model.get("memory_storage_allowed", True)) and relevance_score >= 3
    if memory_allowed:
        state.future_session_memory = [*state.get("future_session_memory", []), memory_entry][-5:]
    if state.get("session_start_time"):
        state.session_duration_minutes = int((time_module.time() - state.session_start_time) / 60)
    state.current_screen = "feedback"
    state.session_complete = False
    state.is_loading = False
    state.answer_evaluation_error = ""
    state.answer_evaluation_notice = ""
    reset_answer_evaluation_state(state)

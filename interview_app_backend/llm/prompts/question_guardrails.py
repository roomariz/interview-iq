from __future__ import annotations


def _example_question(question_type: str) -> str:
    if question_type == "behavioural":
        return (
            "You are leading a delivery team and a release slipped because two engineers disagreed on the API contract. "
            "How would you handle the conflict, keep the work moving, and make sure the next release stays on track?"
        )
    if question_type == "system_design":
        return (
            "You are designing a customer-facing platform that must handle a sharp spike in traffic during a launch event. "
            "How would you design the system, balance reliability with cost, and decide which trade-offs to accept?"
        )
    if question_type == "follow_up":
        return (
            "You mentioned the rollout was delayed because the monitoring data was unclear. "
            "How would you tighten the observability, confirm the root cause, and reduce the risk of the same issue happening again?"
        )
    return (
        "You are working on a customer-facing web application where users report that submitting forms becomes slow during peak hours. "
        "The backend service handles database writes and validation logic. How would you investigate the issue, identify the root cause, "
        "and improve performance without affecting system stability?"
    )


def build_question_guardrails_block(question_type: str) -> str:
    example = _example_question(question_type)
    return (
        "HARD_CONSTRAINTS:\n"
        "- The question MUST describe a concrete, real-world scenario.\n"
        "- The question MUST start with a situation such as \"You are working on...\" or \"Your team is...\".\n"
        "- The question MUST NOT be generic or abstract.\n\n"
        "SOFT_VALIDATION:\n"
        "- Before finalising, check whether the question clearly reflects the selected role.\n"
        "- If CV is provided, use explicit technologies, projects, or responsibilities mentioned in the CV.\n"
        "- If JD is provided, reflect real responsibilities from the JD rather than generic wording.\n"
        "- Avoid vague phrases such as \"based on your experience\".\n"
        "- Do not reuse the same opening style as previous questions.\n"
        "- If any check fails, revise the question before output.\n\n"
        "FINAL CHECK (MANDATORY):\n"
        "- If CV exists, the question MUST reference at least one explicit CV skill, project, or responsibility.\n"
        "- If JD exists, the question MUST reflect at least one specific JD requirement or responsibility.\n"
        "- If both exist, prioritise overlap or explicitly probe a gap.\n"
        "- If any condition is not satisfied, regenerate the question.\n\n"
        "FORBIDDEN_PATTERNS:\n"
        '- "How would you apply your experience"\n'
        '- "Explain your approach"\n'
        '- "What would you do in general"\n'
        "- Any question without a clear scenario\n\n"
        "QUESTION_STRUCTURE:\n"
        "1. Context (system, feature, or situation)\n"
        "2. Problem (failure, constraint, or requirement)\n"
        "3. Task (what the candidate must do)\n\n"
        "EXAMPLE_QUESTION_STYLE:\n"
        f"\"{example}\"\n\n"
        "FINAL_CHECK BEFORE OUTPUT:\n"
        "- Does the question describe a specific situation? (YES/NO)\n"
        "- Does it include a clear problem? (YES/NO)\n"
        "- Is it free from generic phrasing? (YES/NO)\n"
        "- If any answer is NO, regenerate the question.\n"
    )

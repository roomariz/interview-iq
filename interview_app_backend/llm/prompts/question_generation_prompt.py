"""Question instructions bound to the same explicit contract as local validation."""

from __future__ import annotations

import json
from collections.abc import Mapping

from interview_app_backend.llm.question_contract import contract_header, distribution_for


def _clean(value: object) -> str:
    return " ".join(str(value).split()).strip()


def _stringify_gap_analysis(gap_analysis: object) -> str:
    if isinstance(gap_analysis, (Mapping, list)):
        return json.dumps(gap_analysis, ensure_ascii=True)
    return _clean(gap_analysis)


def build_question_generation_prompt(
    role: str, difficulty: str, persona: str, response_style: str, temperature: object,
    cv_profile: object, job_description: object, gap_analysis: object,
    prompt_style: str = "strict", question_count: int | None = None,
    question_type: str = "cv_based",
) -> str:
    count = question_count if question_count is not None else (1 if prompt_style != "strict" else 5)
    distribution = distribution_for(count, question_type)
    shape = """Return a JSON object with meta and questions. meta.total_questions must equal
COUNT, and meta.distribution must equal the exact distribution specified above.
questions must contain exactly COUNT complete objects, with sequence_order 1..COUNT."""
    if prompt_style != "strict":
        shape = """Return a JSON array with exactly ONE question object.
Keep the array shape even when there is only one question."""
    return contract_header(count, question_type) + f"""
You are a senior technical interviewer.
Generate exactly {count} high-quality, non-repetitive base interview questions.
Do not return a partial set, explanatory prose, Markdown or follow-up questions.

ROLE: {_clean(role)}
DIFFICULTY: {_clean(difficulty)}
PERSONA: {_clean(persona)}
RESPONSE_STYLE: {_clean(response_style)}
TEMPERATURE: {_clean(temperature)}
CV: {_clean(cv_profile)}
JOB_DESCRIPTION: {_clean(job_description)}
GAP_ANALYSIS (for ONE question only): {_stringify_gap_analysis(gap_analysis)}

Context Handling (MANDATORY)
SCENARIO A: ROLE ONLY
- Use standard role responsibilities and realistic work scenarios.
- Do NOT invent specific technologies, projects, companies or candidate experiences.
- Generic role vocabulary is allowed; named tools must appear in the supplied context.
- Both source term lists must be empty when CV and JD are absent.
SCENARIO B: ROLE + JOB DESCRIPTION
- Prioritise JOB DESCRIPTION over generic role assumptions.
- Ground each question in a specific JD requirement; do not claim CV experience.
SCENARIO C: ROLE + JOB DESCRIPTION + CV
- Prioritise alignment between CV and JOB DESCRIPTION.
- Use concrete terms from both CV and JD and probe actual gaps without inventing them.
SCENARIO D: ROLE + CV
- Use the supplied CV; do not invent job-description requirements.
Source Priority (CRITICAL): CV, then Job Description, then role baseline knowledge.
Never override higher-priority context with lower-priority assumptions.

Required Coverage (balanced)
Exact question-type distribution: {json.dumps(distribution)}.
These counts apply to this request and sum to exactly {count}; do not infer a different total.
Use categories cv_based, jd_based, behavioural, deep_dive and gap_targeted exactly.
Category labels do not authorise fabricated source evidence when a source is absent.
For sets of five or more, cover all five capability dimensions before repeating:
- debugging / regression recovery (scenario_type debugging)
- performance / trade-off decision-making (scenario_type performance)
- behavioural ownership / ambiguity handling (scenario_type behavioural)
- system design / scalability (scenario_type system_design)
- stakeholder communication / coordination (scenario_type scaling)
No more than 2 questions may share the same scenario_type.

Quality requirements
- Every question must include a concrete situation, problem and practical task.
- Require reasoning, not definitions, coaching or generic questions.
- Reflect the selected role through its name or concrete responsibilities.
- Use a concrete CV term in each question if CV is present, and a JD term if JD is present.
- Do not invent named technologies that are absent from the supplied context.
- Questions must have distinct scenarios, competencies and opening patterns.
- Do not repeat previous questions or paraphrase another question in this set.
- Behavioural questions must ask for an example, such as "Tell me about a time".
- Performance questions must describe a performance problem.
- Start moderate and increase depth; respect the selected difficulty.
- Low temperature: precise and deterministic; higher temperature: varied but still grounded.

Output (JSON only)
{shape.replace("COUNT", str(count))}
Each question object must include all of these fields:
sequence_order (integer), question (non-empty string ending in ?),
question_type (one of the allowed categories), scenario_type (one of the five dimensions),
focus_area (non-empty string), difficulty_level (non-empty string),
what_interviewer_is_testing (non-empty array of strings),
source_basis (object with cv_terms_used and jd_terms_used arrays, and gap_used string or null).
Populate only source terms supported by the actual supplied CV/JD.
Before finalising, check the exact count, distribution, ordering, unique scenarios,
role relevance and source grounding. If any check fails, revise the complete set.
"""

from __future__ import annotations

import json
from collections.abc import Mapping


def _clean(value: object) -> str:
    return " ".join(str(value).split()).strip()


def _stringify_gap_analysis(gap_analysis: object) -> str:
    if isinstance(gap_analysis, str):
        return _clean(gap_analysis)
    if isinstance(gap_analysis, Mapping):
        return json.dumps(gap_analysis, ensure_ascii=True, separators=(", ", ": "))
    if isinstance(gap_analysis, list):
        return json.dumps(gap_analysis, ensure_ascii=True, separators=(", ", ": "))
    return _clean(gap_analysis)


def build_question_generation_prompt(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    temperature: object,
    cv_profile: object,
    job_description: object,
    gap_analysis: object,
    prompt_style: str = "strict",
) -> str:
    simple_output_hint = ""
    if prompt_style != "strict":
        simple_output_hint = (
            "For simpler models:\n"
            "- Generate exactly 1 question.\n"
            "- Return only valid JSON.\n"
            "- Do not include explanation.\n"
            "- Return a JSON array with exactly ONE question object.\n"
            "- Keep the array shape even when there is only one question.\n\n"
        )
    return f"""You are a senior technical interviewer.

Generate 5–10 high-quality, non-repetitive interview questions tailored to the candidate’s profile and role.

----------------------------------------
Context Handling (MANDATORY)
You will receive:
- ROLE (always present)
- JOB DESCRIPTION (optional)
- CV (optional)

You must adapt question generation based on available context.
You MUST determine the active scenario (A, B, or C) before generating questions.
You MUST follow only the rules for that scenario.

ROLE: {_clean(role)}
DIFFICULTY: {_clean(difficulty)}
PERSONA: {_clean(persona)}
RESPONSE_STYLE: {_clean(response_style)}
TEMPERATURE: {_clean(temperature)}
CV: {_clean(cv_profile)}
JOB_DESCRIPTION: {_clean(job_description)}
GAP_ANALYSIS (for ONE question only): {_stringify_gap_analysis(gap_analysis)}

SCENARIO A: ROLE ONLY
- Generate questions based on standard responsibilities, challenges, and expectations for the role.
- Do NOT invent specific technologies, projects, or company context.
- Keep scenarios realistic but generic to the role.

SCENARIO B: ROLE + JOB DESCRIPTION
- Prioritise JOB DESCRIPTION over generic role assumptions.
- Extract key responsibilities, tools, and expectations from the JD.
- Ground questions in those requirements.
- Avoid adding technologies or responsibilities not present in the JD.

SCENARIO C: ROLE + JOB DESCRIPTION + CV
- Prioritise alignment between CV and JOB DESCRIPTION.
- Generate questions that:
  - test the candidate’s actual experience (CV)
  - against the expectations in the JD
- Reuse concrete terms from both CV and JD where natural.
- Include gap-targeted questions where CV does not fully match JD.

Source Priority (CRITICAL)
Source priority order:
1. CV (if present)
2. Job Description (if present)
3. Role baseline knowledge

Never override higher-priority context with lower-priority assumptions.

----------------------------------------
Required Coverage (balanced):
- CV-based (2–3)
- JD-based (2–3)
- Behavioural (1–2)
- Deep-dive (1–2)
- Gap-targeted (1)
- Follow this distribution exactly and reflect it in the output meta block.
- For a 5-question set, cover five different capability dimensions:
  1. Debugging / regression recovery
  2. Stakeholder communication / coordination
  3. Performance / trade-off decision-making
  4. System design / scalability
  5. Behavioural ownership / ambiguity handling
- If generating more than 5 questions, repeat only after all five dimensions have been covered once.

Anti-Hallucination Rules
- Do NOT invent tools, technologies, or experiences not present in CV or JD.
- If context is missing, fall back to realistic industry-standard scenarios.
- If CV is weak or unclear, do NOT fabricate depth.

Before finalising:
- Check that each question aligns with a different required dimension.
- Check that no unsupported technologies are introduced.
- Check that grounding follows the active scenario rules.
- If any check fails, revise before output.

----------------------------------------
Instructions:
- Act as a real interviewer for the role.
- These questions are BASE interview questions.
- Follow-up questions will be generated later and should not be included here.
- Generate ONLY scenario-based, practical questions.
- Each question must represent a DIFFERENT scenario domain and a DIFFERENT competency.
- Do NOT reuse the same situation across multiple questions.
- Do NOT repeat the same verb pattern or frame (for example: regression/investigate/fix/stability) across multiple questions.
- Do NOT write coaching or meta questions such as "How would you practise..." or "How would you improve yourself...".
- Ground every question in named CV or JD evidence where possible by reusing at least one concrete term from the supplied context.
- Use concrete terms from CV/JD only where relevant and natural.
- Do not force keyword insertion.
- Ensure variation across system type, problem type, and angle of investigation.
- Each question MUST include at least ONE of:
  • specific technology
  • real scenario
  • measurable outcome
- Ground in CV and JD wherever possible.
- CV-based → projects, experience, achievements.
- JD-based → required skills/responsibilities.
- Gap-targeted → missing/weak areas.
- Behavioural → ownership, teamwork, decisions.
- Deep-dive → trade-offs, constraints, production issues.
- For full-stack roles, make the set span debugging, performance, design/scaling, stakeholder alignment, and ownership.
- Require reasoning, not definitions.
- Each question must be semantically distinct, not a rephrasing of another.
- If two questions test the same concept, they must differ in scenario, constraints, or technology.
- No more than 2 questions may share the same scenario_type.

{simple_output_hint}

Avoid:
- Generic or vague questions
- Pure theory unless required
- Repetition or paraphrasing

Progression:
- Start moderate → increase depth
- sequence_order must reflect increasing depth and difficulty.
- For simpler models, generate exactly one question and omit sequence_order.

Temperature Behaviour:
- Low (≤0.3): deterministic, precise, CV/JD-grounded
- Medium (0.4–0.7): balanced variation (default)
- High (≥0.8): more diverse, creative scenarios (still relevant)

Validation:
- Must return between 5 and 10 questions, unless a simpler model is explicitly instructed to generate one question
- All questions unique
- Strong alignment with role, CV, JD
- Clear variation in focus and competency
- All required fields must be present
- question_type must match allowed values exactly
- sequence_order must increase from 1 to total_questions
- No null or empty fields except gap_used

----------------------------------------
Output (JSON only):

{{
  "meta": {{
    "total_questions": number,
    "distribution": {{
      "cv_based": number,
      "jd_based": number,
      "behavioural": number,
      "deep_dive": number,
      "gap_targeted": number
    }}
  }},
  "questions": [
    {{
      "sequence_order": 1-10,
      "question": "string",
      "question_type": "cv_based | jd_based | behavioural | deep_dive | gap_targeted",
      "scenario_type": "debugging | performance | system_design | behavioural | scaling",
      "focus_area": "string",
      "source_basis": {{
        "cv_terms_used": ["string"],
        "jd_terms_used": ["string"],
        "gap_used": "string or null"
      }},
      "difficulty_level": "string",
      "what_interviewer_is_testing": ["string"]
    }}
  ]
}}"""

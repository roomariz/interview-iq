# Question relevance investigation

## Root cause and pipeline trace

The actual question was not replaced in the normal submission path. The defect
was a fixed evaluation target inside the semantic relevance prompt.

1. `interview_app_frontend/state/session_manager.py::submit_answer` takes
   `current_question` and the trimmed answer and submits both to a worker through
   `state/answer_evaluation_job.py::begin_answer_evaluation`. The normal path
   passes those strings directly; role, difficulty, CV, reference answers and
   session memory are not arguments to relevance classification.
2. `EvaluationPipeline.run` validates the inputs and calls `run_relevance_stage`.
   The keyword preclassifier offers a diagnostic signal, not semantic evidence.
3. Previously, `evaluation_rules.py::_semantic_relevance_match` included the
   real question but always asked whether the response addressed **system
   performance, constraints and measurable results**. A model could correctly
   reject that invented target while the candidate answered the real question.
   A bare NO immediately overrode local overlap, without evidence or confidence.
4. On rejection, `relevance_gate.py::build_relevance_gate_evaluation` and
   `pipeline_output.py::attach_relevance_gate` inserted fixed performance feedback
   and a measurable-results follow-up. The “original system-performance question”
   description was template text, not evidence of a cached previous question.
   The gate skipped evidence extraction, reference generation and full scoring.
5. On acceptance, `evaluation_service.py::evaluate_answer` previously ran another
   relevance check. Two model calls could disagree about the same submission.
6. Scoring prompts and two consistency checks also treated missing metrics as
   low specificity for every question type. Follow-up validation matched issue
   keywords rather than the actual question. These reinforced the incorrect rubric.

There is no relevance cache or conversation-history input in this path. Reference
answers are generated after relevance, and future-session memory is stored after
feedback; neither explains the original gate. A missing `current_question` still
uses the existing frontend default question. That separate fallback is unchanged.
The original provider response/log was not supplied, so its literal NO cannot be
verified retrospectively. The supplied output matches the deterministic gate.

## Implemented behaviour

- `relevance_assessment.py` builds a question-bound semantic prompt and validates
  the response with Pydantic. It distinguishes behavioural, technical knowledge,
  troubleshooting, design and optimisation questions. Relevant, partial,
  off-topic and uncertain verdicts are separate from answer quality.
- Off-topic gating requires confidence >= 0.85, a reason and non-empty exact
  quotes from both inputs. Empty answers remain rejected. Unavailable, malformed,
  ambiguous and unsupported negative verdicts are uncertain, never keyword-only
  failures. Legacy YES is accepted; bare NO cannot justify a severe penalty.
- One assessment flows through scoring. Scoring cannot independently assert an
  off-topic gate or substitute another question: contradictions produce the
  existing retry error without recorded scores, rather than invented replacements.
- Non-behavioural specificity uses concrete applicable steps and decisions;
  missing historical metrics no longer imposes the specificity cap. STAR and
  historical outcomes are not required for hypothetical technical scenarios.
- Follow-ups use the original question and submitted response. Troubleshooting
  probes ask which logs, metrics or traces distinguish causes and guide recovery.
  No synthetic follow-up grounding percentage is assigned.
- Uncertain relevance yields low decision confidence and provisional reliability.
  Confirmed off-topic output retains low scoring trust and high decision confidence.
  Nested trust duplication is removed; warning/detail/summary values are aligned.
  Provider metadata is cleared before classification to avoid stale attribution.

## Files changed for this fix

Backend services: `relevance_assessment.py` (new), `question_followup.py` (new),
`evaluation_rules.py`, `evaluation_service.py`, `evaluation_pipeline.py`,
`relevance_gate.py`, `pipeline_output.py`, `evaluation_interpretation.py`,
`evaluation_grounding.py` and `evaluation_decisions.py`.

Tests: `relevance_regression_fixtures.py` and `test_relevance_regression.py` (new);
updated `test_evaluation_pipeline.py`, `test_out_of_scope_evaluation.py`,
`test_ollama_workflows.py` and `test_semantic_similarity_evaluation.py`.
Documentation: this report, the three manuals and the constraint log in `AGENTS.md`.
Earlier staged provider/question-generation changes were retained.

## Regression coverage and validation

The fixture contains the user's verbatim question and answer and the reported
incorrect evaluation fields, including the original incorrect follow-up. No
production rule recognises this fixture or forces it to pass.

The new tests cover all five question types, no metrics/STAR, partial relevance,
genuine unrelated responses, uncertain/malformed verdicts, invalid quotations,
provider outage, cross-question isolation, contradictory scoring, grounded
follow-ups and confidence/reliability consistency. Mocked Gemini, Ollama and
OpenRouter transports and opt-in Ollama-to-OpenRouter fallback exercise the same
contract for relevant and off-topic answers. External inference is blocked.

Validation: the new regression module passes **24 tests**. The combined evaluation,
parser, confidence, Gemini, Ollama, OpenRouter and Grok run passes **164 tests**,
with the known bare-Streamlit submission-state test deselected. Run with
`LLM_PROVIDER=open-router` using `.venv/Scripts/python.exe -m pytest`;
provider-specific tests select their provider explicitly. Changed-file lint passes
apart from the existing unused `trust_block` in `evaluation_interpretation.py`.
`git diff --check` passes and all files touched by this fix remain <=250 lines.

The full repository suite is not green: an unrelated logger test expects a warning on the client module
logger but the existing transport emits it on `llm`. The legacy Streamlit
submission test also fails to populate bare-session state. Broad runs stalled
after the example-answer tests and were stopped; focused evaluation/provider
verification completes normally. Existing service lint findings include an unused
`trust_block` and facade imports; they were not removed as unrelated cleanup.

## Remaining limitations

Semantic judgements and question-type classification still depend on the model;
quoted text and self-reported confidence cannot prove a semantic judgement correct.
Provider failures leave relevance unresolved and feedback provisional. They cannot
reliably establish genuine off-topic behaviour during an outage.

Provider transport and fallback tests use mocks, not live Gemini/Ollama/OpenRouter
acceptance. Providers may return different JSON formatting or question-type
judgements; invalid outputs follow the same uncertain path. No integration,
frontend layout or provider fallback policy was changed. No deployment occurred.

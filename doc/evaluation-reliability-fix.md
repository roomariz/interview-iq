# Evaluation reliability investigation

The later [confidence correction](evaluation-confidence-correction.md) supersedes
the confidence-based verdict and feedback-suppression rules described below.

Local changes, 16 November 2026. No deployment or live inference was performed.
Existing Streamlit screens and provider transports were preserved.

## Confirmed causes

The user's complete live JSON is preserved in
`tests/fixtures/live_evaluation.json`. The unrelated caching, denormalisation,
messaging, scaling and queue advice exactly matches `DEFAULT_FEEDBACK` in
`feedback_model.py`. Its `_merge_list()` substituted demo text for valid empty
lists. Its default strengths included “not relevant to the question”. This is a
confirmed UI normalisation defect; the original raw provider completion was not
supplied, so attributing every original sentence to Gemini would be unsupported.

Other confirmed defects:

- `normalise_feedback_payload()` ignored root `trust`, instead reading decision
  detail or a removed nested trust object. A categorical score-confidence string
  became numerical zero while the warning retained 0.75.
- `classify_fallback_failure()` ended with unconditional `low_specificity`.
- `build_fallback_review_state()` inferred confidence from answer scores and
  supplied definitions that could contradict the chosen trust level.
- `apply_evaluation_consistency()` replaced contradictions with additional
  unproven weaknesses, including STAR advice and missing decision reasoning.
- `_restrict_low_grounding_feedback()` asserted candidate deficiencies merely
  because evaluation support was weak.
- `_evaluation_confidence()` averaged evidence coverage into confidence, treating
  absent metrics, alternatives and other rubric features as uncertainty.
- `build_follow_up()` inferred a repeat gap from memory length and overwrote
  question-bound probes with unrelated system-performance/metrics templates.
- `_apply_answer_feedback()` already respected `memory_storage_allowed`, but
  normalisation defaulted permission to true without validation or trust checks.
- The parser defaulted example answers to `{}`; the UI converted that to text.

## Pipeline and data boundaries

| Stage | Functions and data |
|---|---|
| Inputs | `EvaluationPipeline.validate_input()` trims question/answer; existing UI input validation remains in place. |
| Relevance and question type | `run_relevance_stage()` obtains the semantic assessment, type and verdict confidence; keyword disagreement remains an uncertainty signal. |
| Evidence | `extract_evidence_context()` passes the actual question/answer to extraction; `build_evaluation_context()` retains numeric evidence and local markers. |
| Scoring | `evaluate_answer()` sends current inputs, type criteria, extracted evidence and optional reference/similarity. Reference similarity does not determine relevance. |
| Parsing | `parse_json_response()` validates the existing nested or flat scoring contract with Pydantic. |
| Normalisation | `ground_evaluation_result()` / `apply_evaluation_consistency()` retain anomaly penalties and remove fabricated low-support guidance. |
| Claim grounding | `validate_feedback_support()` requires a matching claim and exact excerpts from both current inputs; malformed, absent or cross-session support withholds the claim. |
| Follow-up | `_ground_follow_up()` / `question_bound_followup()` produce a neutral question-bound depth probe, without asserting a missing capability. |
| Final reconciliation | `attach_pipeline()` calls `finalise_evaluation()` to synchronise confidence, aliases, failure scope and memory permission. |
| UI and memory | `normalise_feedback_payload()` preserves empty lists and root trust; `build_key_takeaway()` withholds established weaknesses when memory permission is false. The existing session writer checks that permission. |
| Serialisation | Existing feedback-screen JSON uses these normalised fields; scores, labels, strengths and improvements now agree with their canonical backend counterparts. |

The end-to-end regression sends the supplied question, answer and faulty payload
through mocked scoring, final output and UI normalisation. Separate tests exercise
multiple question types and relevance gates. No expected production score or
feedback sentence was hardcoded as a replacement answer.

## Final invariants and memory policy

- Empty strengths/issues/improvements stay empty. No demo evidence is substituted.
- Scoring prompts request `feedback_support` records containing `claim`,
  `answer_quote` and `question_quote`. Pydantic validates their shape; excerpts
  must occur verbatim in the current inputs. Claims without support are withheld.
- Additional output checks remove known unsupported technologies/techniques,
  high-relevance/off-topic wording, invented metric assertions and inappropriate
  STAR/historical-results demands. High-score labels cannot assert a weak dimension.
- Strong specificity does not imply `low_specificity`. An evaluation reliability
  warning has `failure_scope=evaluation_reliability`, with an explicit provisional
  explanation; it is not an established candidate weakness.
- All numerical `score_confidence` aliases agree, including decision detail.
  Conflicting values are reconciled conservatively using the lower value.
- `grounding_score` is the scoring-support alias. `evaluation_confidence.relevance`
  means confidence in the semantic verdict; `completeness` is observed coverage,
  not confidence. `overall` is the lower of relevance and scoring confidence.
- `decision_confidence` is a verdict-confidence category. Confirmed off-topic
  decisions remain high confidence with zero detailed-scoring support.
- Missing confidence remains unavailable/provisional; high candidate scores do not
  manufacture evaluation confidence. Trust definitions agree with the final level.
- Memory requires explicit permission, checked non-empty feedback, medium/high
  trust, scoring confidence at least 0.4, no high-severity warning and no relevance
  gate. Any withheld claim blocks new memory conclusions for that evaluation.
- Empty/malformed example answers become an empty string. Genuine prose remains
  text. The example-generation service uses the same guard.

## Question generation

`validate_generated_items()` now applies performance rules to the declared
performance scenario, rather than an incidental `focus_area` label on another
capability. Behavioural/system-design checks also follow scenario classification,
not the unrelated provenance categories `cv_based`, `jd_based` or `deep_dive`.

`validate_question()` recognises concrete production/release/team/service
situations with problem or change cues, alongside its original scenario forms.
Named-tool restrictions, source grounding, coverage, distribution and duplicate
checks remain active. Retry errors identify the question and explain the concrete
situation/problem/task requirement. Performance scenarios still require a
performance problem; role-only scenarios still reject invented named tools.

## Faulty output versus corrected replay

See [corrected JSON](evaluation-corrected-replay.json). This is a local replay of
the supplied payload, not a fresh Gemini assessment or a claim of increased trust.

| Field | Original | Corrected replay |
|---|---|---|
| Scores / score-based decision | 9/8/8/9/8; pass | Preserved; provisional |
| Failure | `low_specificity` despite specificity 8 | `hallucination_risk`, explicitly scoped to evaluation reliability |
| Detailed feedback | Irrelevance strength and unrelated technical advice | Unsupported claims withheld; lists empty |
| Score confidence | `high`, 0.75 and 0.0 | Numerical 0.0 consistently; uncertainty preserved |
| Trust definition | High-confidence definition with low trust | Low/provisional definition |
| Follow-up | Unsupported repeat gap | Current regression, diagnostic evidence and recovery probe |
| Memory | Stores irrelevance/metrics takeaway | Permission false; no new conclusion |
| Example | String `"{}"` | Empty string |

## Changed files

- Backend services: `evaluation_service.py`, `evaluation_pipeline.py`,
  `pipeline_output.py`, `evaluation_rules.py`, `evaluation_decisions.py`,
  `evaluation_interpretation.py`, `evaluation_grounding.py`, `trust_defaults.py`,
  `question_validation.py`, `question_quality.py`.
- Added services: `feedback_support.py`, `feedback_integrity.py`,
  `evaluation_output.py`; moved scoring/extraction constants to
  `llm/prompts/evaluation.py` to keep file sizes below 250 lines.
- Schemas/parsing: `llm/parser.py`, `llm/prompt_contract.py`, `models/evaluation.py`.
- UI helpers: `feedback_model.py`, `feedback_view.py`; no screen layout changes.
- Tests: added `test_feedback_integrity_regression.py` and the exact live JSON;
  updated parser, semantic-similarity, calibration, scenario, trust, UI-trust and
  role-generation tests for the new contracts.
- Documentation: this report, corrected replay, three manuals and the AGENTS log.

## Validation and limits

The combined affected test selection, including mocked Google and Ollama transport
tests, passed **274 tests**. External network access is blocked by the test suite.
Ruff found **zero introduced findings** against HEAD; six existing unused-variable
or unused-import findings remain in interpretation and older trust test modules.
All files changed in this task remain below 250 lines.

The full-suite attempt stopped at an unrelated existing provider logging assertion:
`test_call_llm_logs_empty_output` expects the client logger, but the message is
emitted by `client_support` on logger `llm`. The complete repository suite is not
reported as passing.

Source excerpts establish provenance, not proof of semantic entailment. Models
can still attach an inappropriate interpretation to a real quote; the local
checks are conservative, not a complete semantic verifier. Unrecognised technical
concepts also require model judgement. Providers that omit the new support records
will yield withheld feedback rather than fabricated replacements. Live compliance
with those instructions, and visual browser acceptance, remain unverified.

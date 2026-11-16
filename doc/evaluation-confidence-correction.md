# Evaluation confidence and coaching correction

16 November 2026. Local implementation and tests only; no deployment or live
provider calls. Existing Streamlit screens and provider integrations are retained.

## Confirmed causes

1. `apply_decision_adjustments()` downgraded a pass when grounding was below 0.4
   or overall confidence below 0.3. It ran twice in the pipeline. This conflated
   performance with evaluator reliability.
2. `_ground_and_enrich()` assigned `hallucination_risk` for low confidence or a
   classifier disagreement. `finalise_evaluation()` also assigned it for any low
   trust level, including incomplete coaching with no identified hallucination.
3. `validate_feedback_support()` matched claim text and source excerpts exactly,
   after contradiction normalisation had changed claim wording. Harmless spacing
   or punctuation differences also caused rejection. The scoring schema example
   omitted the support records that the prose instructions required.
4. `_restrict_low_grounding_feedback()` erased all coaching at low confidence,
   including independently supported strengths and improvements. There was no
   bounded correction path when support records were absent.
5. `EvaluationSchema` and the nested prompt-contract adapter omitted `criteria`.
   The UI's correct empty-list preservation exposed that missing contract field.
6. `build_evaluation_context()` discarded the extractor's numerical confidence,
   substituting presence-based constants. `_score_confidence()` then added bonuses
   for deep reasoning and penalties for shallow reasoning. `_trust_level()` could
   also lower trust for weak measurable impact, conflating answer characteristics
   with evaluator certainty.
7. `question_bound_followup()` deliberately embedded the entire original question
   in every positive probe and used broad diagnostic templates instead of an
   actual answer decision.

The full original JSON remains unchanged in `tests/fixtures/live_evaluation.json`.
It contains the earlier conflicting confidence values and unsupported advice.
The latest report supplies scores but no new complete raw provider response; its
exact source-extraction confidence and validation flags cannot be reconstructed.
The 0.75 clean-assessment path is therefore tested explicitly alongside the full
original fixture, rather than presented as a replay of an unavailable response.

## Corrected behaviour

### Performance and reliability

The final candidate verdict comes from the existing five-dimension score rules.
Evaluator uncertainty never changes it. A confirmed relevance gate still fails
the answer. Low-quality scores still fail normally; all-zero scores no longer
default to pass.

`assessment_status` and `provisional` express evaluator uncertainty separately.
The root verdict, nested verdict, decision detail and evaluation summary agree.
`gating_applied` at the final output refers to the relevance gate, not confidence.

Numerical score confidence uses the actual extraction confidence, with applicable
consistency/anomaly penalties. Missing metrics are not an applicable requirement
for hypothetical technical answers. Reasoning depth and measurable impact no
longer manufacture confidence bonuses or force low trust.

At 0.75 with no material issues, trust is medium under the existing thresholds;
the numerical value remains 0.75 and the score-based verdict remains unchanged.
Material contradictions, genuine unsupported claims and uncertain relevance can
still lower trust. Confidence remains a heuristic support measure, not a calibrated
probability that a model's assessment is correct.

### Traceable warnings

`failure_reasons` records concrete reasons for `hallucination_risk`, such as
unsupported technology, incompatible score/feedback claims, unsupported metric
assertions, mismatched source quotes or misleading/fake metric flags.
`reliability_issues` records the corresponding validation actions and uncertainty.
Missing support records, low confidence, empty coaching and keyword/semantic
classifier disagreement alone do not establish hallucination.

The UI keeps the existing short provisional-assessment copy. Detailed diagnostic
codes stay in the structured evaluation; they do not become candidate weaknesses.

### Useful coaching

- The scoring schema explicitly includes strengths, criteria and support records.
- Support matching normalises Unicode, case, whitespace and trailing full stops;
  it still rejects excerpts from different questions or answers.
- Source support is checked before wording normalisation, avoiding rejection just
  because the normaliser rewrote an accepted claim.
- Low numerical confidence does not erase independently validated coaching.
- Missing/incomplete coaching receives at most one feedback-only repair request
  through the selected provider. The request includes the current inputs and
  validation issues, and cannot update scores, relevance or trust values.
- Accepted original coaching survives an incomplete repair. New claims require
  valid source excerpts and pass the same output checks. Unsupported weaknesses
  remain excluded; empty issue arrays are valid.
- If repair fails, scores remain intact and incomplete coaching is explicitly
  provisional. No favourable feedback or weakness is fabricated.
- Criteria are selected for the assessed question type, including diagnostic
  evidence, recovery and verification for troubleshooting; STAR is not imposed.

Memory continues to require validated feedback and sufficient trust. Low-trust
or unsupported conclusions are not treated as established weaknesses.

### Specific follow-ups

Positive probes use an actual answer excerpt and, where available, the validated
coaching focus. The regression example now probes the choice between rollback and
disabling the affected feature. Technical-knowledge, design and behavioural probes
use their respective answer context. Full question/answer provenance remains in
`context_note`; the visible question does not need to repeat it.

## Modified files

Backend services:

- `evaluation_decisions.py`, `evaluation_pipeline.py`, `evaluation_rules.py`:
  performance verdicts, risk classification and follow-up wiring.
- `evaluation_output.py`: final confidence/verdict reconciliation, provisional
  status, traceable risk reasons and reliability issues.
- `evaluation_signals.py`, `evaluation_interpretation.py`: preserve extraction
  confidence and remove performance-based confidence bonuses/trust caps.
- `evaluation_grounding.py`: retain supported coaching at low confidence.
- `feedback_support.py`, `feedback_integrity.py`: tolerant provenance matching,
  reasoned claim removals and validation metadata.
- New `feedback_repair.py`: bounded coaching repair and question-type criteria.
- `question_followup.py`: concise answer-specific probes.
- `evaluation_service.py`: validation order, feedback repair and criteria.

Contracts and UI data:

- `llm/prompts/evaluation.py`, `llm/parser.py`, `llm/prompt_contract.py`:
  consistent feedback/support/criteria contract.
- `interview_app_frontend/utils/feedback_model.py`: retain assessment status.
  Screen layouts and provider transports are unchanged.

Tests and documentation:

- Added `test_performance_reliability_separation.py` (20 cases).
- Updated feedback-integrity, relevance, pipeline, refinement, scenario, parser
  and semantic-similarity tests for preserved coaching and concise probes.
- Updated the three manuals, AGENTS decision log and prior investigation link.

## Validation

**294 tests passed** across the affected evaluation/parser/UI/memory, question
generation and mocked Google/Ollama provider selections. This includes strong
answers at 0.0/0.2/0.44/0.75 confidence, supported feedback at low confidence,
missing citations, actual unsupported advice, invalid/failed repairs, clean 0.75
trust, concise follow-ups across question types, off-topic gates and low scores.

Ruff reports no newly introduced findings. Its one finding in files touched by
this correction is the existing unused `trust_block` in
`evaluation_interpretation.py`. `git diff --check` passes. All files changed by
this correction remain below 250 lines. The complete repository suite was not
rerun; the earlier unrelated provider-logger assertion remains outside this scope.

## Remaining limits

Source excerpts establish provenance, not semantic entailment. A model can still
misinterpret a genuine quote. Repair adds at most one logical provider request
when coaching is incomplete, using existing transport retry behaviour. Providers
may still omit usable support on both attempts; that result remains incomplete
and provisional. Live Gemini compliance and visual browser acceptance were not
tested, and the source excerpt/technique checks do not recognise every possible
unsupported claim.

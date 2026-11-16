# Question generation validation fix

## Root cause and trace

1. The UI job uses the configured model profile. Gemini has a five-question
   session and requests a five-question bundle. The existing OpenRouter free
   profile retains three session questions generated one at a time.
2. The old active prompt asked for 5–10 questions, while its category minimums
   required at least seven (2 CV + 2 JD + 1 behavioural + 1 deep-dive + 1 gap).
   It also retained a one-question instruction and a one-item output example.
   None of these encoded the actual requested five-question count in the wire schema.
3. Gemini previously received JSON-object mode only. There was no Pydantic question
   schema binding the request's array length, metadata count and distribution.
   The strict legacy parser accepted only 5–10 items and returned an empty list
   for partial/malformed bundles, losing the validation reason.
4. `_filter_question_items` could discard questions for role/context/scenario
   failures and reconstructed items with empty source metadata. Duplicate handling
   then replaced any set below five with an empty list. The final bundle validator
   reported `invalid_question_count` for that empty list.
   **The old “Generated questions” log showed post-filter survivors, not raw Gemini
   output. One/two entries in that log do not prove the raw response had that size.**
5. Each retry sent the same prompt without explaining which rule failed.
6. Role-only validation treated every word in a broad vocabulary as invented
   technology, including ordinary role terms such as `backend` and `performance`.
   That contradicted role relevance and could reject otherwise grounded questions.
7. Existing backup builders did not enforce all normal generation checks. Some
   paths explicitly logged a validation warning and returned invalid items anyway;
   the job also had a separate unchecked backup builder.
8. The worker's cancellation lambda captured Streamlit session state and called
   `state.get()` on the background thread, producing `missing ScriptRunContext`.

## Count, category and capability contract

Gemini's normal UI request remains **exactly five base questions**. A five-question
bundle contains one each of `cv_based`, `jd_based`, `behavioural`, `deep_dive` and
`gap_targeted`, matching the existing five-category backup cycle. It must also
cover debugging, performance, behavioural ownership, system design and scaling /
stakeholder coordination, with no repeated dimension in a five-question bundle.
Category labels never authorise invented CV/JD facts when those sources are absent.

Single-question APIs request exactly one question; session length is a separate
setting. Explicit 5–10-item requests retain coverage-before-repeat and the existing
maximum of two questions per scenario type. No two-question or partial bundle is
accepted as a five-question interview. Future weighted-distribution documentation
and the separate question-distribution helper are not used to reinterpret this
active generation contract and were not changed.

## Changes

- `question_contract.py` defines Pydantic items, source basis, metadata and bundles.
  It checks the exact requested count, complete fields, order, duplicate text,
  category totals and agreement between metadata and actual questions.
- The active prompt now has one explicit count and matching integer category totals.
  Every public request passes its actual per-call count. A trusted first-line
  contract binds Google transport schema and retry validation to the same request.
- Google question requests use its documented `json_schema` response format,
  including exact `minItems`/`maxItems` and equal numeric bounds on metadata totals.
  Business checks still run locally: role relevance, scenarios, named technologies,
  source terms, previous-question similarity, opening patterns and semantic duplicates.
  Metadata is retained rather than discarded while filtering.
- Ollama still omits unsupported server-side schema enforcement; it validates
  locally against the same requested contract. OpenRouter routing and model
  rankings are unchanged. Gemini evidence/scoring validation is unchanged.
- Failed attempts request a **complete corrected replacement**, naming the count,
  JSON, field, duplicate or scenario failure. No synthetic items pad a partial set.
  Permanent provider errors stop provider retries; cancellation is honoured before
  a request, after a response and before backup generation.
- Ordinary role vocabulary is distinguished from named tools. Invented tools and
  unsupported CV/JD source claims remain rejected. Dimension and question-type
  checks are preserved, including the existing `deep_dive` design intent.
- Existing backup candidates now pass the same applicable schema, exact count,
  quality and duplicate checks. If they fail, the worker returns no questions and
  the UI uses its existing setup/retry error flow. Invalid items are never returned
  as successful model output. No new backup question bank or evaluation scores
  were introduced.
- The UI thread creates the cancellation `Event` and snapshots mutable context.
  Workers receive plain data, the captured backend callable and `Event.is_set`.
  No Streamlit state, rendering or navigation is accessed by the worker.
- The pre-existing 1,736-line question service, 443-line job module and 570-line
  loop test module were split to honour the project's 250-line rule. Compatibility
  interfaces retain existing service imports and test patch points; unrelated
  helper behaviour was moved intact. The Streamlit interface was not redesigned.

## Verification

- Focused generation/provider/UI regression command: **122 passed**.
- Final full offline suite: **402 passed, 9 failed, 11 deselected**.
- Saved pre-change baseline: **374 passed, 13 failed, 11 deselected**.
  Every remaining failing test ID was already failing in that baseline; there are
  no newly failing test IDs. Related legacy tests were updated to assert exact
  request counts, preserved context and rejection of unsafe backup results.
- Ruff passes for every Python file changed in this fix. `git diff --check` passes.
  Added/modified Markdown and Python files stay within 250 lines.
- API calls in tests are mocked, including a real OpenAI SDK client backed by
  `httpx.MockTransport`. It verifies that a one-question response is rejected,
  the correction identifies `expected 5, received 1`, both requests carry exact
  Google JSON Schema bounds, and a valid five-question replacement passes.
- Regressions cover partial/extra counts, malformed JSON, missing fields, wrong
  category totals, duplicate detection, unsupported named tools/source claims,
  positive/negative backup validation, source-metadata preservation, cancellation,
  snapshot isolation and the existing Google/OpenRouter/Ollama/Grok paths.

Reproduce the new regressions with the project's virtual environment:

```powershell
$env:LLM_PROVIDER='open-router'
python -m pytest tests/test_question_contract_regression.py tests/test_question_google_contract.py tests/test_question_worker_snapshot.py -q
```

The test-process provider override keeps legacy defaults deterministic; tests
select Google/Ollama explicitly when required. It does not change the application's
private `.env`. Default pytest excludes live and browser tests, and an external
socket guard prevents inference requests.

## Remaining limitations

- **No live Gemini request was made for this fix.** Actual API schema acceptance,
  model quality, project quotas and account access remain unverified.
- Google documents structured-output support for `gemini-3.5-flash-lite` and array
  bounds, but schema support is a subset and semantic correctness still requires
  local checks. See [model capabilities](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite),
  [structured output](https://ai.google.dev/gemini-api/docs/structured-output) and
  [OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).
- The existing template bank may not contain a complete valid backup for every
  role/context. The application now stops safely instead of displaying an invalid
  or duplicated set. It does not manufacture extra questions to meet the count.
- The existing 30-second UI job timeout is unchanged. Slow or quota-limited requests
  can therefore reach the existing recovery path.
- Bare-mode Streamlit warnings can still appear on the **main thread** in unit
  tests that deliberately run without `streamlit run`; worker state access is
  covered by a thread-bound state regression rather than warning suppression.
- Nine existing failures remain in logging/SDK assertions, out-of-scope evaluation,
  semantic similarity and sample-answer state tests. No deployment was performed.

## Files modified or added for this fix

- `AGENTS.md`
- `doc/developer-manual.md`
- `doc/manual.md`
- `doc/test-manual.md`
- `interview_app_backend/llm/google_chat.py`
- `interview_app_backend/llm/ollama_client.py`
- `interview_app_backend/llm/prompts/question_generation_prompt.py`
- `interview_app_backend/llm/question_contract.py`
- `interview_app_backend/services/question_bundle.py`
- `interview_app_backend/services/question_constants.py`
- `interview_app_backend/services/question_context.py`
- `interview_app_backend/services/question_fallback.py`
- `interview_app_backend/services/question_fallback_templates.py`
- `interview_app_backend/services/question_generation_job.py`
- `interview_app_backend/services/question_grounding.py`
- `interview_app_backend/services/question_job_payload.py`
- `interview_app_backend/services/question_job_poll.py`
- `interview_app_backend/services/question_job_result.py`
- `interview_app_backend/services/question_job_worker.py`
- `interview_app_backend/services/question_prompt_helpers.py`
- `interview_app_backend/services/question_quality.py`
- `interview_app_backend/services/question_requests.py`
- `interview_app_backend/services/question_retry.py`
- `interview_app_backend/services/question_service.py`
- `interview_app_backend/services/question_session_requests.py`
- `interview_app_backend/services/question_similarity.py`
- `interview_app_backend/services/question_validation.py`
- `tests/question_contract_fixtures.py`
- `tests/question_loop_support.py`
- `tests/test_full_question_loop.py`
- `tests/test_google_provider.py`
- `tests/test_ollama_workflows.py`
- `tests/test_question_contract_regression.py`
- `tests/test_question_control_layer.py`
- `tests/test_question_fallback_ui.py`
- `tests/test_question_generation.py`
- `tests/test_question_generation_retry.py`
- `tests/test_question_generation_scenarios.py`
- `tests/test_question_google_contract.py`
- `tests/test_question_loop_navigation.py`
- `tests/test_question_loop_rendering.py`
- `tests/test_question_loop_widgets.py`
- `tests/test_question_sequence_progression.py`
- `tests/test_question_worker_snapshot.py`
- `tests/test_role_based_question_generation.py`
- `doc/question-validation-fix.md`

## Follow-up: role-only rejection and backup failure

The reported successful Google calls now fail semantic validation rather than
question-count parsing. The user confirmed that neither CV nor JD was supplied.
The legacy technology check scanned broad capability words with substring matches:
`monitoring` could be rejected as an unsupported tool, and `reaction` could match
`react`. The logs do not contain the model text, so the exact term in those three
responses cannot be reconstructed. Named-tool detection now uses word boundaries;
raw supplied context must authorise named tools, independently of semantic groups.
Role relevance, source grounding and scenario checks remain active.

The backup generator labelled its second item as performance but passed the general
focus and selected a production-incident template without performance wording.
Its behavioural item could also fall through to a technical template. Role-only
backup scenarios now explicitly cover debugging, performance, behavioural examples,
design and scaling/coordination, without asserting CV/JD experience. Per-item focus
matches the assigned scenario. All candidates still pass the full contract and
quality checks, including duplicate detection; failure remains closed.

Retries identify the question index and unsupported named tool, allowing the model
to correct that specific issue. No provider settings, UI or evaluation scores change.

Additional files for this follow-up: `services/question_grounding.py`,
`services/question_validation.py`, `services/question_quality.py`,
`services/question_fallback.py`, `services/question_fallback_templates.py` under
`interview_app_backend`; `tests/test_role_only_grounding_regression.py`,
`tests/test_question_generation_retry.py`, `tests/test_question_generation_scenarios.py`;
and the three manuals plus this report.

No live Gemini request was made for this follow-up. Document-backed backup sets
can still fail when the existing templates cannot satisfy all source requirements.

Follow-up verification: 34 new regression cases pass, including five- and
ten-question backup sets across four roles and three difficulty settings. The
full offline suite reports 436 passed, 9 failed and 11 deselected. The same nine
failure IDs were recorded before this follow-up. Ruff and `git diff --check` pass.
All 12 follow-up files remain within 250 lines. No deployment was performed.

# Test Manual

## Manual Checks

1. Follow [Phase 2 local setup](phase2-integration.md): start FastAPI on port 8000 and Streamlit separately, with matching server secrets and `BACKEND_API_URL`.
2. Confirm the welcome heading and browser tab title both show InterviewIQ.
3. Click `Start Setup`; confirm the setup screen appears and its left panel shows InterviewIQ aligned left beside the logo.
4. Toggle `st.session_state.has_active_session` to `True` and refresh the app.
5. Confirm the alternate welcome state shows resume and new session actions.
6. Expand the advanced configuration section on setup and confirm the detected tech stack is shown before any manual override.
7. Start an interview and confirm the app first shows the preparing screen with the role, CV, and job-description checks before moving on.
8. Confirm the question screen shows the generated provider/model source line after the question loads.
9. Submit a valid answer and confirm the screen switches to a locked evaluation state with a blurred overlay and loading message before feedback appears.

## Expected Result

- The app opens without errors.
- Screen routing works through the frontend layer.
- Session state initialisation remains stable.

## Basic Verification

- Run `python -m py_compile app.py interview_app_frontend/app.py`.
- Run `pytest tests/test_session_manager.py` to verify restart and exit behaviour.
- Run `pytest tests/test_environment_loading.py` to verify both API key settings are loaded safely from the environment.
- Run `pytest tests/test_full_question_loop.py` to verify navigation state persists through the app entry point.
- Open the app in Playwright or a browser and confirm the welcome screen eventually renders the full card, CTA button, and helper text.
- Confirm `Start Setup` uses the same primary blue styling as `Start Interview`.
- Confirm the question screen renders the sidebar, question card, answer box, and disabled submit button styling.
- Confirm the question screen shows the provider/model source line for the generated questionnaire.
- Confirm the answer warning, textarea, character count, and action buttons stay grouped inside one bordered answer card.
- Confirm typing into the answer box enables `Submit Answer`, and clearing the text disables it again.
- Confirm the locked evaluation screen replaces the answer editor with a `Your Answer (submitted)` expander instead of leaving the live textarea visible.
- Confirm the in-app `Request Log` shows the answer-evaluation request while the feedback screen is locked.
- Confirm the `Request Log` stays hidden on the preparing and question screens.
- Confirm the `Request Log` auto-expands while answer evaluation is running on screens where it is visible.
- Confirm the setup, question, and feedback screens reuse the same sidebar component, while welcome remains sidebar-free.
- Confirm the setup sidebar stays muted while the question and feedback sidebars use the active white-card styling.
- Confirm the setup screen no longer shows an extra session card beneath the shared sidebar.
- Confirm the sidebar shows the detected tech stack, focus areas, and active question type without exposing raw competency weights.
- Confirm the question and feedback sidebars show green completion badges for Job Description and CV when those fields are marked as added or uploaded.
- Confirm the shared CSS is applied after reload on Windows and Linux, so the sidebar, cards, and buttons render with the mockup styling instead of plain text.
- Confirm clicking `Start Interview` with missing required fields keeps the app on the setup screen and shows the validation message.
- Confirm the role field shows only the required asterisk, with no separate inline "Role is required." error text.
- Confirm the role selector still works after a refresh and does not raise a Streamlit segmented-control deserialisation error.
- Confirm stale setup widget keys are cleared before the app renders, even though the live widgets now use the same tab-style control pattern.
- Confirm the advanced tech-stack selector now uses `setup_tech_stack_selection_v2`, while the app clears the older setup widget keys so stale button-group state from an older run does not crash reruns.
- Confirm the submit button stays disabled until the answer reaches 50 characters and passes validation.
- Confirm Clear remains available when the answer field is empty.
- Confirm the validation warning appears only when the inline guard blocks the current answer.
- Confirm the question header icon, meta row, sidebar statuses, and action buttons match the `3-Question & Answer.png` mockup.
- Confirm the question title badge uses the star-style badge and the question text reads larger, closer to the reference image.
- Confirm the question screen keeps the setup-style top bar so the setup-to-question transition feels like a content change rather than a layout jump.
- Confirm the setup and question screens now share the same top bar structure, with only the copy changing between them.
- Confirm the question panel now fills the full width of the right-hand container and does not leave a large empty gap on the right.
- Confirm the answer safety notice sits on the same line as the answer heading instead of taking a separate row.
- Confirm generic question phrasing is rejected and the fallback question still reads as a concrete scenario when the LLM response is too abstract.
- Confirm the preparing screen shows a spinner/progress state and adapts its checklist when only the role, role plus CV, or role plus CV plus job description are available.
- Confirm the question-generation prompt now includes `PRIORITY_ORDER`, `PREVIOUS_QUESTIONS`, and the `QUESTION_PLAN` block with `Type`, `Purpose`, and `Focus`.
- Confirm the question-generation payload now includes `meta.total_questions`, `meta.distribution`, and per-question `sequence_order`, and that invalid counts are rejected.
- Confirm a blank LLM response writes an `llm_empty_output` warning with provider, model, and output length.
- Confirm `XAI_API_KEY` is read from the repo `.env` and Grok is tried after OpenRouter when a direct client is needed.
- Confirm the question-generation payload also includes `scenario_type`, and that repeated scenario types are capped so collapsed multi-question runs retry and then fall back safely.
- Confirm the question-generation prompt distinguishes role-only, role-plus-JD, and role-plus-JD-plus-CV scenarios, and that unsupported technologies are rejected by output validation.
- Confirm a deliberately slow generation path still shows “We prepared a backup question to keep your session smooth.” after the longer wait limit and then switches to a fallback question without overwriting the fallback later.
- Confirm fallback questions still read as concrete scenarios and include role, CV, or job-description keywords when those inputs are present.
- Confirm repeated opening styles such as “Describe a time...” and “Describe a situation...” are rejected as the same question pattern.
- Confirm the Back, Submit Answer, and Clear buttons share the same height in the answer card.
- Confirm the character count line has tighter top and bottom spacing beneath the answer field.
- Confirm the answer card stays inside the right-hand main panel beneath the question card.
- Confirm the setup temperature slider no longer emits the empty-label accessibility warning.
- Confirm the question view Back to Setup button returns to the setup screen without clearing the saved setup selections.
- Confirm clicking `Start Interview` no longer shows the `Calling st.rerun() within a callback is a no-op` warning.
- Confirm the answer field is shorter than before and still keeps the warning, character count, and buttons grouped.
- Confirm the setup and question screens fit the browser window better after the reduced vertical spacing changes.
- Confirm the question screen now fits more comfortably on a shorter Windows-sized browser window, with a smaller answer box and tighter card spacing.
- Confirm the setup screen no longer adds extra top space compared with the question screen, so the transition feels smoother.
- Confirm the question metadata stays on one line and the Back button appears in the same row as Submit and Clear.
- Confirm the sidebar container is shorter on setup and interview screens while retaining the same alignment.
- Confirm the sidebar leaves a little more room for the main panel after the latest height reduction.
- Confirm the setup sidebar no longer leaves a large blank area beneath the configuration items.
- Confirm the setup sidebar item and button spacing now matches the shared interview sidebar more closely.
- Confirm the sidebar Restart and Exit Session buttons work on the question and feedback screens.
- Confirm the interview sidebar shows the selected role, difficulty, persona, response style, and optional job/CV status chosen on setup.
- Confirm blocked answers show the inline validation banner beneath the answer area.
- Confirm the setup screen no longer emits a browser permissions-policy warning when you click `Start Interview`.
- Confirm an active session opened on the welcome screen now routes straight to the question screen.
- Confirm the `launch_question_view` flag is cleared after the question screen renders.
- Confirm a stale `?screen=question` query parameter does not pull the app back from feedback after an answer is submitted.
- Confirm the question screen shows the warning banner by default and displays `—` for Job Description and CV until session data is populated.
- Confirm `st.session_state.feedback` with structured evaluation data routes the app to the feedback screen.
- Confirm an invalid API key or LLM outage leaves the user on the question screen and shows the inline evaluation-failure warning instead of an exception page.
- Confirm the configured `MODEL_NAME` in the repo `.env` is used for OpenRouter requests, that the client uses `https://openrouter.ai/api/v1`, and that question generation prefers Llama 3 8B, then Mistral 7B, then Gemma 3 12B before falling back to `openai/gpt-5-nano` if needed.
- Confirm evaluation uses the Google-only free chain `google/gemma-4-31b-it:free` -> `google/gemma-3-12b-it:free`, and reports an evaluation error without placeholder scores if all models fail.
- Confirm malformed-but-repairable JSON is repaired before fallback, while invalid schema still fails with a validation log that includes the model, validation status, and reason.
- Confirm a transient failure such as 429 or a timeout retries the same model with exponential backoff, while 400/403 fail fast and model-unavailable errors move to the next configured model.
- Confirm the app logs the resolved OpenRouter model at startup so the Streamlit console shows which model is active.
- Confirm OpenRouter logs now use a structured `status=... task=... provider=... model=...` format, so question generation and evaluation calls are distinguishable in the console.
- Confirm the feedback screen keeps all content inside the right-hand panel, shows the score breakdown, strengths, weak points, improvement notes, and displays the technical JSON section expanded by default.
- Confirm the feedback screen places `Your Question` and `Your Answer (submitted)` inside collapsed expanders, while keeping the technical JSON section expanded by default.
- Confirm the feedback screen now shows trust level, score confidence, decision confidence, and reasoning depth before the score breakdown.
- Confirm clicking `Show Example Answer` from the feedback screen opens the improved-answer screen.
- Confirm the feedback screen now renders the follow-up card and uses one reasoning block rather than repeating the same fields.
- Confirm the feedback screen now shows a compact score-consistency note when the visible decision and score-based verdict differ.
- Confirm the follow-up card is generated from the weakest score, issue context, and reasoning depth when the payload does not include a follow-up question.
- Confirm the strengths block shows the strongest signals first.
- Confirm the session summary shows readable focus areas rather than internal weighting details.
- Confirm the question submit button is disabled when the answer field is empty and becomes enabled once text is entered.
- Confirm clicking Clear resets the answer box immediately.
- Confirm clicking `Submit Answer` with a valid answer routes to the feedback screen without clearing the draft before the transition.
- Confirm clicking `Submit Answer` first shows the locked evaluation overlay, then lands on feedback once the background evaluation completes.
- Confirm the improved-answer screen shows the question, submitted answer, and stronger answer in read-only cards.
- Confirm `Back to Feedback` returns to the feedback screen and `Next Question` keeps the session flow available.
- Run `pytest tests/test_evaluation_parser.py` to verify structured evaluation schema parsing.
- Confirm the evaluation prompt passes the question and answer into the OpenRouter call, extracts evidence first, and scores against the structured evidence context.
- Confirm the relevance pre-classifier can short-circuit clearly off-topic answers before the scoring prompt runs.
- Confirm `evaluate_submission()` returns `evaluation_pipeline` with explicit stage order, `grounding_score`, and `evaluation_confidence`.
- Confirm `failure_type` and `evaluation_summary` are present, and low grounding can downgrade a pass to borderline pass.
- Confirm the feedback screen shows a compact, read-only reliability card under Overall Outcome with no raw percentages and an assessment label instead of a signal label.
- Confirm classifier conflict lowers trust and is surfaced in `validation_warning["anomaly_flags"]`.
- Confirm follow-up questions are re-grounded against the detected issue context rather than left blank.
- Confirm metric-heavy answers stay aligned with the evidence context and that contradiction flags, anomaly flags, and confidence scores are returned in the evaluation payload.
- Confirm trust and decision confidence are grounded against the evidence context rather than accepted directly from raw model output.
- Confirm fallback numeric detection flags ambiguous metrics, fake-looking metrics, and non-impact numbers in the evaluation context.
- Confirm misleading metrics surface as `misleading_metrics` and push validation severity to `high`.
- Confirm `validation_warning` also includes trust level, reasoning depth, and dimension-level contradiction buckets.
- Confirm `evaluation_version`, `evaluation_trace`, and `impact_strength` appear in the parsed evaluation output.
- Confirm the calibration dataset is present, valid, and used for deterministic helper checks rather than LLM calls.
- Confirm `overall_decision_detail` preserves the visible decision while exposing trust level, score confidence, and decision confidence.
- Confirm reasoning depth now supports `none`, `implicit`, `developing`, `explicit`, and `deep`.
- Confirm anomaly influence is returned as a machine-readable object and that score normalisation stays disabled by default.
- Run `python3 -m unittest tests.test_semantic_similarity_evaluation` to verify the model-assisted extraction contract, contradiction logging, and rewritten feedback wording.
- Run `python3 -m pytest tests/test_evaluation_parser.py` to verify both the legacy parser output and the new prompt-contract JSON shape.
- Run `pytest tests/test_report_service.py` to verify the report download payload.
- Run `pytest tests/test_session_summary.py` to verify session summary aggregation.
- Run `pytest tests/test_feedback_screen.py` to verify feedback formatting, score mapping, and feedback routing.
- Confirm the direct evaluator path still uses a single OpenRouter client call, while out-of-scope answers short-circuit to the hard relevance gate.

## Phase 1 offline verification

1. Install `requirements-dev.txt` into the project virtual environment.
2. Run the focused pytest command in [Phase 1 integration](phase1-integration.md).
   Calls are mocked and external socket connections are blocked, including during
   background worker shutdown.
3. Run `python -m uvicorn api.index:app --reload` and open
   `http://127.0.0.1:8000/api/health`; expect `{"status":"ok"}` without LLM credentials.
4. Launch Streamlit as usual and verify the existing setup, question, feedback and
   example-answer screens. No frontend request should target FastAPI in Phase 1.
5. Use mocked workflow tests for success, invalid JSON, relevance checks,
   authentication errors, timeouts, rate limits and opt-in OpenRouter fallback.
6. Confirm exhausted evaluations display the existing retry error and do not save
   placeholder scores. Provider changes require restarting the application.
7. With a local Ollama `OLLAMA_HOST` already set in Windows, confirm the project
   `.env` value `OLLAMA_HOST=https://ollama.com` resolves to the cloud host after restart.
   `tests/test_ollama_configuration.py` covers this conflict without API calls.
8. Confirm a project `.env` Ollama key overrides a different inherited key, while
   environment-only credentials still work. Use the configuration tests; do not
   print credentials or make a live inference request to test precedence.

Default pytest runs exclude `live` and `e2e` tests. Do not enable live API tests
for automated verification. Windows in-process API tests require local loopback
access for asyncio. No live provider request is required for these checks.

## Direct Grok checks

Run `python -m pytest tests/test_grok_provider.py` with `LLM_PROVIDER=open-router`
in the test process to keep unrelated legacy defaults deterministic. Grok tests
select their provider explicitly and use mocked responses. Verify model selection,
xAI URL, bearer authentication, `store=false`, evidence/scoring validation and
authentication failure without automatic OpenRouter fallback. After changing the
application provider, restart Streamlit and confirm the private `XAI_API_KEY` is
a valid xAI API credential. Do not print the key or run paid automated inference.

## Direct Gemini checks

Run `python -m pytest tests/test_google_provider.py` with `LLM_PROVIDER=open-router`
in the test process; the tests select Google explicitly and use mocked responses.
Verify Google model configuration, the Chat Completions endpoint, JSON-object mode,
Pydantic validation, empty/truncated output rejection, quota/timeout retry limits
and the lack of automatic paid-provider fallback. Existing OpenRouter Google
models must continue using the OpenRouter Responses API. After setting the private
`GOOGLE_API_KEY`, restart Streamlit and check the log reports provider `google`.
No live API call is needed for automated checks.

## Question contract regression checks

Run `python -m pytest tests/test_question_contract_regression.py
tests/test_question_google_contract.py tests/test_question_worker_snapshot.py -q`
as one command, with `LLM_PROVIDER=open-router` in the test process. Tests select
Google explicitly when required, use mocked HTTP and block external inference.
Confirm partial/malformed responses retry with an exact reason, the Google request
contains JSON Schema bounds, and invalid backup candidates return a setup error.
Check that worker cancellation and mutable context do not access Streamlit state.
Live Gemini acceptance has not been tested as part of this fix.

Run `python -m pytest tests/test_role_only_grounding_regression.py -q` offline.
Start a session without CV/JD: check all five dimensions, including a slowdown
and a behavioural example request. Confirm generic monitoring/reaction wording
is accepted, invented named tools are rejected with an indexed correction, and
provider failure uses validated backup scenarios. Repeated/invalid backups fail.

## Release-regression relevance checks

Run `.venv/Scripts/python.exe -m pytest tests/test_relevance_regression.py -q`
offline with `LLM_PROVIDER=open-router`. Use the verbatim fixture in
`tests/relevance_regression_fixtures.py` in the UI: expect no off-topic gate, no STAR
or historical-result demand, and a diagnostic evidence follow-up. Check unrelated
answers still fail when confirmed, uncertain verdicts display low reliability,
and provider fallback follows the same contract. No live inference is required.

## Feedback integrity regression

Run `.venv/Scripts/python.exe -m pytest tests/test_feedback_integrity_regression.py -q`.
Replay `tests/fixtures/live_evaluation.json`: empty feedback must stay empty;
no caching/scaling advice, irrelevant strength, `{}` example or repeat-gap probe
may appear as validated feedback. Low trust must prevent new memory entries.
Check numerical score confidence agrees across trust, warning and decision detail.
Use a genuinely unrelated answer to verify the off-topic gate still fails it.
See [investigation and comparison](evaluation-reliability-fix.md).

## Performance versus reliability regression

Run `.venv/Scripts/python.exe -m pytest tests/test_performance_reliability_separation.py -q`.
With a strong answer, check that low evaluator confidence retains the score-based
verdict and shows provisional status. At 0.75, a clean assessment has medium trust
and no hallucination classification. Check supported coaching remains visible,
unsupported advice has a recorded reason, and rollback/disable follow-ups are short.
Criteria must match the question type. Failed coaching repair must not alter scores.

## Phase 2 HTTP verification

Run `.venv/Scripts/python.exe -m pytest tests/test_phase2_api.py tests/test_phase2_client.py tests/test_phase2_workflow.py tests/test_phase2_llm_integration.py tests/test_phase2_local_streamlit.py -q`.
These tests mock providers; the local Streamlit test uses a real Uvicorn loopback server.
See [results and known baseline failures](phase2-test-results.md).
Complete an interview with a mocked backend: setup, question, answer, feedback,
next question and summary. Check provider metadata and follow-up remain visible.
Try an invalid answer and oversized CV; neither should produce scores.
Stop FastAPI and retry setup: a friendly connection error must appear.
Change the frontend secret: setup must fail without exposing credentials.
Open two browser sessions: answers, context and adaptation must remain independent.
Check `/docs` for schemas and authentication; health remains unauthenticated.
Do not use real providers for manual checks without explicit permission.

## Phase 3A readiness and Phase 5 controls
Run `tests/test_phase5*.py` with `PHASE5_REDIS_PORT=16389` and disposable Redis. URL regressions reject different endpoints; `scripts/verify_phase5_redis.py` uses four configured PINGs only when explicitly run. See [replacement verification](phase5-replacement-preview.md); deployment/inference await approval.

Run `python -m pytest tests/test_phase3_deadlines.py tests/test_phase3_rate_limit.py tests/test_phase3b_deployment.py -q`.
With mocked providers, exhaust a short deadline and check the retry notice.
Across two instances, verify a combined 429 quota and 503 on shared-service outage.
See [Phase 3A verification](phase3a-test-results.md) and [real Redis checks](phase3b-upstash-setup.md); [dependency upgrade verification](dependency-security-review.md) and [reconciled baseline tests](test-failure-assessment.md). The opt-in Redis script now checks expiry and invalid credentials; no live provider calls authorised. Follow [Phase 4A verification](phase4a-verification.md) for signed identities, global quotas, real Redis multi-process admission, lease expiry and logging privacy.

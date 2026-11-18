# Developer Manual

## Scope

Phase 2 separates Streamlit and FastAPI through authenticated HTTP; see [contracts, local setup and Vercel review](phase2-integration.md), [file inventory](phase2-files.md) and [test results](phase2-test-results.md). CI pins Ubuntu 24.04 for Playwright 1.53.x.

## Files

- `app.py`: root launcher; welcome heading, browser title and `APP_TITLE` use InterviewIQ.
- `interview_app_frontend/app.py`: Streamlit entry point.
- `interview_app_frontend/ui/screens.py`: screen routing.
- `interview_app_frontend/components/shell.py`: screen shell, setup layout, CV paste handling, and top-level CTA placement.
- `interview_app_frontend/components/sidebar.py`: shared sidebar renderer with InterviewIQ text aligned left beside its logo, used by setup, question, and feedback screens.
- `interview_app_frontend/components/question_panel.py`: compact right-hand question panel renderer for the question screen.
- `interview_app_frontend/components/answer_evaluation_screen.py`: locked evaluation screen that polls the background answer-evaluation job.
- `interview_app_frontend/components/feedback_screen.py`: feedback screen renderer for the diagnostic view, collapsible question and submitted-answer sections, and report download.
- `interview_app_frontend/components/sample_answer_screen.py`: improved-answer learning reference screen.
- `interview_app_frontend/state/session_manager.py`: HTTP setup, submission and session initialisation; pure helpers, feedback storage and navigation are split into neighbouring modules.
- `interview_app_frontend/state/answer_evaluation_job.py`: background answer-evaluation job helper and polling state.
- `interview_app_backend/llm/prompts/question_generation.py`: unchanged question prompt builder; pure context helpers are shared through `shared/interview_context.py`.
- `interview_app_backend/services/question_sequence.py`: internal question-plan selection, context resolution, and previous-question tracking.
- `interview_app_frontend/state/question_generation_job.py`: HTTP workers receive copied context; session futures and polling stay in Streamlit. Legacy backend jobs remain for compatibility tests.
- `api/interview.py`: stateless context, question, evaluation and example-answer adapters to existing backend services; bearer authentication, bounded requests and local abuse controls protect each operation.
- `interview_app_backend/llm/`: LLM client, parser, and prompts.
- `interview_app_backend/llm/prompt_contract.py`: prompt-contract JSON normaliser for the evaluator output.
- `interview_app_backend/models/evaluation.py`: evaluation shape and core scoring dimensions.
- `interview_app_backend/services/relevance_preclassifier.py`: deterministic first-pass relevance classifier.
- `interview_app_backend/services/evaluation_grounding.py`: evidence-grounded trust and decision normaliser.
- `interview_app_backend/services/evaluation_decisions.py`: decision adjustment, failure classification, and simplified evaluation summary helpers.
- `interview_app_backend/services/evaluation_service.py`: structured answer evaluation orchestration with confidence-aware extraction and anomaly surfacing.
- `interview_app_backend/services/evaluation_pipeline.py`: explicit evaluation controller for validation, relevance, grounding, and follow-up stages.
- `interview_app_frontend/utils/feedback_model.py`: feedback payload normalisation, trust exposure, follow-up extraction, and score mapping helpers.
- `interview_app_frontend/utils/pipeline_view.py`: user-facing reliability copy for the compact feedback card.
- `interview_app_frontend/utils/feedback_view.py`: derived feedback helpers for consistency notes, issue-aware follow-ups, and strength ranking.
- `interview_app_frontend/utils/feedback_styles.py`: CSS for the feedback layout.
- `interview_app_backend/models/report.py`: downloadable report shape.
- `interview_app_backend/services/report_service.py`: JSON report builder for session summaries.
- `interview_app_backend/models/session.py`: session summary data shape.
- `config/settings.py`: runtime settings, including the repo `.env` values for `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`, and `MODEL_NAME`.

## Behaviour

- Session state is initialised from a defined schema.
- `app.py` is a thin launcher and `interview_app_frontend/app.py` remains the Streamlit entry point.
- `interview_app_frontend/app.py` no longer writes temporary debug state to the page before rendering.
- Prompts are isolated from the frontend.
- Question generation now uses an explicit structured template with `PRIORITY_ORDER`, `TECH_STACK`, `TARGET_COMPETENCIES`, and `QUESTION_TYPE`, while still falling back to CV/JD inference when the override is blank.
- OpenRouter calls now use `MODEL_NAME` from the repo `.env` instead of the hard-coded `openrouter/auto` placeholder, the client points at `https://openrouter.ai/api/v1` with app attribution headers, and task-aware fallback chains are split between generation and evaluation.
  - **Question generation chain:**
    - `google/gemma-4-31b-it:free`
    - `google/gemma-3-12b-it:free`
    - `openai/gpt-5-nano`
  - **Evaluation chain:**
    - `google/gemma-4-31b-it:free`
    - `google/gemma-3-12b-it:free`
- `config.settings` now exposes `GOOGLE_API_KEY` and `XAI_API_KEY` as optional empty-string settings so the shared client module can import cleanly when Google or Grok access is not configured.
- `interview_app_backend/llm/provider_clients.py` centralises the Google Gemini and Grok client factories so services can fall back between providers.
- `interview_app_frontend/app.py` now logs the resolved OpenRouter model during startup.
- `interview_app_backend/llm/client.py` now accepts a task label on `call_llm()`, emits structured OpenRouter logs with `status=... task=... provider=... model=...`, retries transient failures with exponential backoff, fails fast on permanent 400/403 errors, validates strict JSON for evaluation tasks, and rotates across the task-specific fallback chain within a 12-second ceiling.
- `interview_app_backend/llm/client.py` now also logs `llm_empty_output` with provider, model, and raw output length when a response comes back blank.
- `interview_app_backend/llm/client.py` also records the final model/provider used on the current worker thread so question generation can log the exact source after completion.
- `interview_app_backend/llm/parser.py` now attempts a light JSON repair before schema validation fails, clamps numeric scores into the 0-10 range, and logs validation events with `evaluation_model=... validation=... fallback_triggered=... reason=...`.
- `Start Interview` now routes to a dedicated `generating_question` screen, starts the first question in a background job, and only promotes the session to the question screen once the future completes.
- Question generation now adds a hard guardrail block with forbidden generic phrases, required scenario structure, a worked example, and a self-check before output.
- Question generation now includes a soft self-validation pass for role, CV, and job-description alignment, plus a `PREVIOUS_QUESTIONS` block and an explicit `QUESTION_PLAN` section with type, purpose, and focus.
- The question-generation parser now enforces the `meta` summary, required fields, count bounds, and `sequence_order` before accepting a response.
- Multi-question generation now hard-deduplicates after parsing, caps repeated `scenario_type` values at two, retries collapsed responses twice, and then falls back to a safe five-question bundle.
- The question-generation service now validates bundle coverage, supported grounding, and unsupported tech terms with a semantic allowance layer before returning generated questions.
- Fallback bundles now pass through the same strict validation path as LLM output, and the service raises `RuntimeError("Fallback generation failed validation")` if the backup set is still invalid.
- Question generation now rejects repeated opening patterns and demands explicit CV or JD grounding instead of vague compliance language.
- The fallback path now uses role-specific templates, respects the selected question type, and can inject CV or job-description keywords when the LLM output is rejected.
- Background question generation now uses a standard `question_job` payload with `status`, `result`, `error`, and `started_at`, plus enforced state transitions, a 30-second timeout, backup-question recovery path, and a warning log that records the root cause when fallback is triggered.
- The first generated question now stores the resolved provider and model in session state, and the question screen shows that source in a small metadata line.
- Answer submission now starts a background evaluation job, shows a locked blurred evaluation screen while the future is running, and finalises feedback once the future resolves.
- The locked evaluation screen now replaces the answer editor with a read-only `Your Answer (submitted)` expander.
- The answer-evaluation request now appears in the in-app Request Log instead of only the console, but the Request Log stays hidden on the preparing and question screens.
- The Request Log auto-expands while an answer-evaluation request is running on screens where it is shown.
- The question text area is keyed directly to `st.session_state.answer`, so the submit button reads the live typed value instead of a stale side channel.
- Inferred tech stack values are shown subtly in the sidebar, but competency weights stay internal and only the readable focus areas are surfaced.
- Adaptation is progressive: repeated weak signals are logged in session state and used to bias later questions without hard-switching the whole flow.
- Backend services are the intended place for future LLM orchestration and processing logic.
- Shared CSS is injected through `st.markdown("<style>...</style>", unsafe_allow_html=True)` so the styles live in the main document.
- The setup screen keeps `Start Interview` clickable and relies on the submission validator to block navigation when required fields are missing.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- The setup screen now uses a mockup-aligned two-column layout with segmented controls, a conditional CV paste field, and a blue theme.
- Use British English in all user-facing text.
- Session restart clears flow-specific state and exit returns the user to the welcome screen after resetting session data.
- `start_interview()` now toggles an `is_loading` session flag during the transition into the question screen.
- The question screen is rendered by `render_question_and_answer()` and now uses a static layout that matches the supplied reference image more closely.
- The answer field is stored in `st.session_state.answer` and the submit button stays disabled until the response reaches 50 characters and passes validation.
- `render_question_and_answer()` now clears the inline warning automatically when the current answer becomes valid again.
- `render_question_and_answer()` displays `st.session_state.answer_submit_error` only when the guard is triggered.
- `render_question_and_answer()` now renders the answer section inside a bordered Streamlit container so the warning, textarea, counter, and buttons stay in one visual card.
- `render_question_and_answer()` now supports a locked evaluation mode with a blurred overlay, disabled controls, and provider/model metadata for the generated question.
- `render_question_and_answer()` now nests the answer card inside the right-hand main panel column, so it no longer spans the full page width.
- `render_question_and_answer()` now reuses the setup-style top bar to keep the setup-to-question transition visually consistent.
- `render_shared_topbar()` now centralises the shared setup/question header so only the copy changes between screens.
- `render_question_and_answer()` now lets the question card fill the full right-hand column instead of capping the width too early.
- `render_question_and_answer()` now places the safety notice on the same line as the answer heading to keep the answer card compact.
- `render_question_and_answer()` now keeps Back, Submit Answer, and Clear at the same button height.
- `render_question_and_answer()` now uses tighter vertical spacing for the character count line beneath the answer field.
- `render_question_and_answer()` now includes a back-to-setup action above the question card and uses a shorter answer field.
- Shared layout spacing has been tightened so the setup and question screens use less vertical height on typical laptop windows.
- `render_question_and_answer()` now trims the question card, answer card, and textarea a little further, with extra compact spacing on shorter viewports so the main panel fits more comfortably.
- The setup shell now keeps the same top spacing as the question screen, so the transition stays smooth without extra blank space.
- `render_question_and_answer()` now keeps the role, difficulty, persona, and focus values on one line, and places Back alongside the answer action buttons.
- The shared sidebar height has been reduced so the sidebar uses less vertical space without changing its structure.
- The sidebar min-height has been trimmed again to free a little more vertical space for the main content.
- The setup sidebar now uses `min-height: auto` so the configuration container hugs its content.
- The setup screen now omits the extra session-only block beneath the shared sidebar, so the sidebar matches the question view more closely.
- The setup sidebar now reuses the shared item and action spacing used by the interview sidebar, so spacing stays consistent across screens.
- `render_question_and_answer()` now uses a star badge, a stronger question heading scale, and a footer divider to better match the mockup.
- `render_interview_sidebar()` now renders real Streamlit restart and exit buttons, and the active screens wire those callbacks through to session reset actions.
- `render_question_and_answer()` and `render_feedback()` now reuse the shared sidebar component and show green completion badges for Job Description and CV when those fields are marked as added or uploaded.
- The shared sidebar now supports muted setup and active question/feedback variants through a single renderer.
- Shared layout CSS is injected in-memory with `st.markdown()` so Streamlit applies the stylesheet without relying on a platform-specific temporary file.
- `submit_answer()` trims the answer, validates length and basic prompt-injection patterns, and appends valid responses to `st.session_state.answers`.
- `render_setup()` no longer injects a scroll-reset iframe script, which avoids browser permissions-policy warnings.
- `render_setup()` now uses versioned setup widget keys such as `setup_role_tabs_v2` and `setup_tech_stack_selection_v2`, which keeps the setup screen visually consistent and prevents stale browser state from hitting an incompatible widget contract on rerun.
- `render_setup()` seeds the visible setup defaults before validation, so the Start Interview button reflects the preselected control values instead of waiting for a manual change.
- `render_welcome()` now renders `Start Setup` as a primary button so it uses the same blue CTA styling as `Start Interview`.
- The role field now relies on the required asterisk in the label instead of a separate inline role validation message.
- `clean_widget_state()` now runs at app startup and clears stale widget state before session initialisation or rendering.
- The setup controls now use tab-style segmented controls for role, persona, difficulty, response style, and CV mode, which keeps the widget state aligned with the current screen design.
- The setup tech-stack multiselect now uses `setup_tech_stack_selection_v2`, and the app clears the older setup widget keys so stale button-group state from older runs does not break reruns.
- `_apply_route_from_query_params()` now applies `screen` only once per session so stale deep links do not overwrite later callback-driven screen changes.
- The setup temperature slider now uses a hidden non-empty label, which removes the Streamlit empty-label warning.
- `start_interview()` now copies the current setup selections into the persistent sidebar values so the interview screens reflect the chosen settings.
- `start_interview()` now relies on Streamlit's automatic callback rerun instead of calling `st.rerun()` inside the button handler.
- `return_to_setup()` returns the user to setup without clearing the saved setup selections.
- `render_screen()` now prefers the question screen when a session is already active, even if `current_screen` falls back to `welcome`.
- `start_interview()` now sets `launch_question_view`, and `render_screen()` consumes that flag to force the question view after the setup callback.
- The question screen keeps the warning banner visible by default and uses `—` for the Job Description and CV sidebar values until real session data exists.
- `render_screen()` now routes to the feedback screen when `st.session_state.feedback` contains structured evaluation data.
- `submit_answer()` now catches evaluation failures, leaves the user on the question screen, and shows a friendly inline warning instead of letting the Streamlit callback crash.
- `render_feedback()` now keeps the full evaluation layout inside the right-hand main column, renders the mock-up-aligned evaluation panel, surfaces trust before the score breakdown, and shows the technical JSON section expanded by default.
- `render_feedback()` now routes the `Show Example Answer` button to the improved-answer screen.
- `render_sample_answer()` renders the question, submitted answer, and stronger example answer in a read-only layout with navigation back to feedback.
- `render_feedback()` now renders a score-consistency warning, a clearer decision-confidence callout, and follow-up guidance as its own card.
- `build_follow_up()` preserves question-bound backend probes; memory count cannot establish repeated gaps.
- `show_sample_answer()` stores the rewritten answer in session state before switching to the improved-answer screen.
- `render_feedback()` now ranks strengths before display so the strongest signals appear first.
- `render_feedback()` now uses a single reasoning block instead of duplicating the same content.
- `submit_answer()` now preserves the drafted answer, stores the submitted question and answer in feedback state, and routes to feedback without blanking the textbox first.
- `render_question_and_answer()` keeps the submit button disabled until the answer field contains text, while the submit handler still enforces validation before routing to feedback.
- `render_question_and_answer()` still uses session-state callbacks for Clear so the answer textbox resets through the normal Streamlit rerun.
- `evaluate_answer()` now sends the question and answer into the evidence-first evaluation prompt, then validates the structured JSON response with Pydantic before returning it.
- `evaluate_answer()` now runs a model-assisted evidence extraction pass first, then scores against an explicit structured `evaluation_context` and returns contradiction and anomaly flags in the evaluation payload.
- `evaluate_answer()` now routes the raw model result through an evidence-grounded trust layer before exposing the payload.
- `evaluate_answer()` now reuses the same OpenRouter client for evidence extraction and scoring, so the request path stays single-shot.
- `evaluate_submission()` now delegates to `EvaluationPipeline`, which makes the stage order explicit and adds pipeline metadata to the returned payload.
- The pipeline now exposes `evaluation_pipeline`, `grounding_score`, `evaluation_confidence`, `failure_type`, and `evaluation_summary`, and it re-grounds follow-up questions against detected issues.
- Grounding and confidence now adjust the final decision when support is too weak, and the frontend receives only a simplified summary of those signals.
- `render_feedback()` now shows a compact reliability card under Overall Outcome rather than raw pipeline metadata, using a small user-facing assessment label.
- The evaluator prompt now asks for the prompt-contract JSON shape, and `parse_json_response()` accepts both that contract and the legacy payload shape.
- `is_answer_relevant()` uses the semantic verdict; deterministic pre-classifier disagreement is an uncertainty signal.
- `build_evaluation_context()` now combines model evidence with local numeric fallback detection, confidence scoring, and structured anomaly flags.
- Validation warnings now carry severity, grouped anomaly flags, and a `score_confidence` indicator.
- Validation warnings now also expose trust level, reasoning depth, and dimension-level contradiction buckets so the flags affect interpretation, not just logging.
- The evaluation payload now carries split validation, trust, and reasoning blocks plus `evaluation_version`, `evaluation_trace`, and `impact_strength`.
- `evaluation_calibration.py` now holds the internal calibration dataset and the helper logic for score-confidence mapping and optional normalisation.
- `overall_decision_detail` preserves the score-based decision value while surfacing trust gating, decision confidence, and review reasons.
- Reasoning depth now spans `none`, `implicit`, `developing`, `explicit`, and `deep`, and anomaly influence is emitted as a machine-readable object.
- Score normalisation is wired in but disabled by default through `NORMALISE_EVALUATION_SCORES`.
- `build_report()` now serialises a session summary into a downloadable JSON report payload.
- `summarise_performance()` now aggregates per-dimension averages and session metadata for the summary screen.
- The session summary now also carries readable focus areas so the UI can show the weakest themes without exposing internal scoring weights.

## FastAPI and Ollama Cloud: Phase 1

- `api/index.py` exposes a credential-free `GET /api/health`; run
  `python -m uvicorn api.index:app --reload` locally. Streamlit is not connected to it.
- `config/settings.py` selects `LLM_PROVIDER` and retains the separate
  `OPENROUTER_MODEL_NAME`, preserving all existing OpenRouter rankings.
- The legacy `get_openrouter_client()` service factory now honours the selected
  provider; `create_openrouter_client()` always creates an OpenRouter SDK client.
- `llm/ollama_client.py` calls the documented cloud HTTP API using `requests`,
  bearer authentication and two bounded attempts. No local server is contacted.
- `gemma4:cloud` maps to the documented direct API model `gemma4:31b`. Other model
  IDs pass through unchanged. Cloud requests omit the unsupported `format` field.
- Question contracts and the existing Pydantic evidence/scoring parsers validate
  cloud output before success or optional fallback. Plain-text relevance, reference
  and example-answer requests retain their existing formats.
- `llm/client_support.py` holds existing response, retry and thread-local metadata
  helpers; `services/pipeline_output.py` holds existing relevance/trust formatting.
- Exhausted evaluation failures raise a safe error for the existing UI error flow.
  The former fabricated 5/10 degraded scores have been removed.
- OpenAI SDK 1.109.1 supports the existing Responses API; evidence calls now use
  the evidence Pydantic schema rather than the scoring schema.
- New provider settings prefer process environment variables, except `OLLAMA_HOST`
  and `OLLAMA_API_KEY`: non-empty project `.env` values override inherited settings.
  Environment-only credentials remain supported. Never log either key value.
  Existing OpenRouter model and timeout precedence remains unchanged.

See [Phase 1 integration](phase1-integration.md) for configuration and checks.

## Direct xAI selection

`LLM_PROVIDER=grok` reuses `provider_clients.get_grok_client()` with
`https://api.x.ai/v1`. `GROK_MODEL` defaults to `grok-4.3` and overrides the retired
legacy Grok model. Dispatch honours the selected provider even when question
services pass their legacy `open-router` argument. The existing OpenAI SDK
Responses API, Pydantic evidence/scoring validation, relevance gates and bounded
retries are reused. xAI requests set `store=false`; no response history is created
through the Responses API. No cross-provider fallback is added for Grok.
`tests/test_grok_provider.py` mocks SDK responses and HTTP transport.

## Direct Google Gemini selection

`LLM_PROVIDER=google` selects the existing Google client with the documented base
URL `https://generativelanguage.googleapis.com/v1beta/openai/`. `GOOGLE_MODEL`
defaults to `gemini-3.5-flash-lite`. `llm/google_chat.py` uses Chat Completions
instead of the Responses API and normalises its output for the existing services.
Question calls request JSON Schema with exact array and metadata counts; evidence
and scoring keep JSON-object mode. All responses are also validated locally.
Empty, blocked or truncated completions fail explicitly. Existing bounded retries
handle rate limits and timeouts; Google has no automatic cross-provider fallback.
`tests/test_google_provider.py` covers mocked SDK/HTTP and evaluation workflows.
Startup logging now reports the selected provider and model without key values.

## Question generation contract

`llm/question_contract.py` owns the explicit per-call count, balanced category
distribution, Pydantic bundle and Google response schema. Generation defaults to
five questions for Gemini and one per call for the existing OpenRouter free profile.
Retries request a complete corrected set and preserve the validation reason.
`services/question_service.py` and `question_generation_job.py` remain compatibility
interfaces; implementations were split into modules below the 250-line limit.
Workers receive plain copied data and an `Event.is_set` cancellation callback;
Streamlit state and routing are only accessed on the main thread. Existing fallback
candidates pass the same schema and quality checks; invalid results fail closed.
See [question validation fix](question-validation-fix.md) for the full trace and tests.

Role-only grounding distinguishes named tools from generic capabilities and uses
word boundaries. Retry errors include the question index and unsupported tool.
Backup generation selects scenario-specific text and focus before validation.

## Reliability references: Phase 5
The optional `deployment/phase5_*` overlays enforce free-only routing and atomic budgets; normal startup does not install them. `phase5_redis.py` compares validated HTTPS roots and effective ports, accepting only empty/root paths; redirects stay disabled. See [replacement preparation](phase5-replacement-preview.md).

See [relevance](relevance-evaluation-fix.md), [feedback](evaluation-reliability-fix.md), [confidence](evaluation-confidence-correction.md) and [Phase 3A production configuration](phase3a-readiness.md), [Phase 3B proposal](phase3b-proposal.md) and [Redis setup](phase3b-upstash-setup.md) and [patched dependencies](dependency-security-review.md) and [local readiness](final-deployment-readiness.md), including quota scope and the unresolved historical Redis anomaly. See [Phase 4A anonymous quotas, leases and private logging](phase4a-report.md) for the current controls and proposed Preview configuration. The request-aware mock preserves adaptive generation; frontend retry preserves the current step. See [implementation and verification](question-progression-investigation.md). See [lease lifecycle verification](redis-lease-investigation.md) for isolated local Redis cancellation/crash tests, the full five-question workflow and corrected harness configuration. Community Cloud preparation now targets the verified mock; see [configuration and runbook](streamlit-community-cloud-proposal.md).

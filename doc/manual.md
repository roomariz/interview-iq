# User Manual

## Overview

Streamlit now communicates with FastAPI over authenticated HTTP. Interview state stays in Streamlit; the screens, scores and provider choices are preserved. See [Phase 2 setup](phase2-integration.md) for both service commands and server-side secrets.

## How To Use

1. Install dependencies with `pip install -r requirements.txt`.
2. Configure the same `BACKEND_API_SECRET` for both servers, start `uvicorn api.index:app --port 8000`, then launch `streamlit run app.py` with `BACKEND_API_URL=http://127.0.0.1:8000`.
3. Start on the InterviewIQ welcome screen and select `Start Setup` to move to the setup screen; its left panel shows InterviewIQ aligned left beside the logo.

## What You Will See

- A welcome screen rendered through the frontend screen layer.
- An active-session welcome state when session state is marked active.
- The `Start Setup` button now uses the same primary blue styling as `Start Interview`.
- A setup screen rendered from the frontend layer, aligned with the setup mockup, blue-accented controls, the conditional CV paste field, and an optional advanced configuration section.
- A preparing screen appears after `Start Interview` and shows the role, CV, and job-description checks before the first question is revealed.
- The sidebar now shows the detected tech stack, inferred focus areas, and the active question type in a subtle read-only summary.
- The question generator now carries previous questions into the prompt so later questions avoid repeating the same pattern.
- The task-aware OpenRouter chain now prefers `google/gemma-4-31b-it:free`, then `google/gemma-3-12b-it:free`.
  - Question generation uses that chain first and can fall back to `openai/gpt-5-nano` as a reliability safety net.
  - Evaluation uses the same free ranking. If every evaluation model fails, the existing error flow asks you to retry without assigning placeholder scores.
  - The shared settings module now also reads optional `GOOGLE_API_KEY` and `XAI_API_KEY` entries from the repo `.env`, which keeps the backend client import stable even when those keys are unset.
- FastAPI resolves the provider and model. Streamlit receives safe model metadata after setup; provider keys belong only on the backend.
- The question-generation log now includes the provider and model that produced the current questionnaire, and the question screen shows that source in a small status line.
- OpenRouter request logs now use a structured `status=... task=... provider=... model=...` format, so you can see which provider answered question generation, evaluation, and related LLM steps, but the Request Log itself stays hidden on the preparing and question screens.
- If the LLM returns no text, the app now logs `llm_empty_output` with the provider, model, and output length to make silent failures easier to trace.
- If OpenRouter is unavailable, the app now tries Grok before falling back to the Google Gemini client.
- The question generation path now falls back across the ranked free chain from multiple providers, then uses `openai/gpt-5-nano` as a reliability safety net when the free chain is exhausted.
- The first-question generation flow now waits longer before timing out, so slower LLM responses have more time to arrive before the backup notice appears.
- The question generation payload now includes a `meta` block and `sequence_order` so the base-question list can stay ordered and count-checked.
- The question generation payload now also carries `scenario_type`, and the backend retries collapsed runs before falling back so the final list stays diverse.
- The question-generation prompt now distinguishes role-only, role-plus-JD, and role-plus-JD-plus-CV scenarios, and the backend validates coverage and grounding before returning.
- The preparing screen now rotates its status messages while a question is being generated.
- If generation takes too long or fails, the app now shows a backup-question notice, keeps the fallback question authoritative, and explains that the backup was prepared to keep the session smooth.
- Fallback questions now follow the selected question plan more closely, using the question type, focus, and previous questions to keep the scenario consistent.
- If a fallback bundle still fails validation, the app now raises a hard error instead of silently returning a weaker set.
- The welcome screen now renders without any temporary debug state output.
- The setup options now use the same tab-style segmented control pattern for role, persona, difficulty, response style, and CV mode, which keeps the setup screen visually consistent and avoids the stale Streamlit selectbox state that caused the refresh-time deserialisation error.
- The setup screen now seeds default selections for the required fields before validation, so the Start Interview button matches the visible preselected controls.
- The role field now relies on the required asterisk in the label instead of a separate inline "Role is required." message.
- The app now uses versioned setup widget keys such as `setup_role_tabs_v2` and `setup_tech_stack_selection_v2`, and it still clears the older setup widget keys at startup so stale Streamlit browser state cannot crash reruns.
- Shared styles are injected directly into the Streamlit document so the interface loads as part of the main page instead of a separate embedded element.

## Current Limits

- The setup screen is still frontend-led, but the layout, helper text, action row, CV paste field, and optional tech stack override now mirror the mockup more closely.
- The interview flow keeps competencies internal, but exposes human-readable focus areas in the feedback and session summary instead of raw weights.
- The system now adapts progressively, so repeated weak signals influence later questions without replacing the whole question mix at once.
- Interview generation, feedback, and reporting flows remain to be wired into the new backend services.
- Session restart and exit now reset the session state back to the welcome flow.
- The interview start flow now exposes a loading flag while the session transitions into the question screen.
- The question screen now mirrors the reference layout with a configuration sidebar, question header, answer area, and action buttons.
- The answer area now sits inside one bordered card so the warning, text box, character count, and buttons stay visually grouped.
- The question and feedback screens now reuse the setup sidebar structure, with only the main content changing between screens.
- The question screen now reuses the setup-style top bar so the transition from setup feels like a content swap rather than a full screen change.
- The setup and question screens now share the same top bar component, which keeps the transition nearly identical apart from the text.
- The question panel now uses the full width of the right-hand container so it no longer leaves a large empty area on the right.
- The answer safety notice now sits on the same line as the answer heading, so the card reads as one compact header row.
- The Back, Submit Answer, and Clear buttons now share the same height in the answer card.
- The character count line now uses tighter top and bottom spacing beneath the answer field.
- The setup sidebar stays muted, while the question and feedback sidebars render in the active white-card state.
- The active question and feedback sidebars now show completion badges for uploaded or added job details, matching the mockups.
- The question generator now rejects generic wording and falls back to a concrete scenario if the LLM response is too abstract.
- The fallback question now stays role-specific and can reflect CV or job-description keywords when they are available.
- The first question is now generated through a background job, so the UI can show a dedicated loading state while the question is being prepared.
- When you submit an answer, the app now switches to a locked evaluation info screen while feedback is being prepared in the background.
- The answer box now keeps the submit button enabled state in sync with the text you type.
- Shared styles are now injected in-memory so the sidebar and card layout render with the intended mockup styling on Windows and Linux.
- `Start Interview` stays visible on the setup screen, but validation keeps the app on setup until the required fields are complete.
- The answer box is wired to session state and the submit button remains disabled until the response reaches 50 characters and passes validation.
- Clear stays available even when the answer field is empty.
- The answer warning banner now stays visible by default, matching the supplied mockup, while still updating when validation blocks the current answer.
- The question header icon, question text scale, and answer-card footer divider now match the supplied mockup more closely.
- The answer card now sits inside the main question panel beneath the question card instead of stretching across the page.
- The setup temperature slider now uses a proper hidden label, so the Streamlit accessibility warning no longer appears.
- The question view now includes a back button to return to setup, and the answer field is shorter.
- The setup and question screens now use tighter vertical spacing so they fit the browser window more comfortably.
- The question screen now uses slightly tighter vertical spacing and a shorter answer box on shorter Windows-sized viewports, so the main panel fits more comfortably.
- The setup screen now keeps the same top spacing as the question screen so the switch feels smoother without adding extra blank space.
- The question header metadata now stays on one line, and the back action sits in the same row as the answer controls.
- The sidebar container now uses less vertical height while keeping the same alignment and content order.
- The sidebar container is now slightly shorter again so it leaves a bit more room for the main panel.
- The setup sidebar now collapses to its content height instead of reserving extra blank space.
- The setup screen now uses only the shared sidebar component, so it matches the question sidebar footprint more closely.
- The setup sidebar item and button spacing now matches the shared interview sidebar more closely.
- The sidebar actions now work in the active interview screens, and the setup selections carry through into the interview sidebar from start to finish.
- The shared sidebar component is now used on setup, question, and feedback screens; welcome remains the only screen without a sidebar.
- The question header icon, meta row, sidebar values, and action buttons now match the supplied question mockup more closely.
- The setup screen no longer triggers a scroll-reset iframe, which avoids the browser permissions warning during setup.
- If a session is already active, the app now prefers the question screen instead of leaving you on the welcome page.
- Clicking `Start Interview` now sets a launch flag so the question screen is shown even if the browser is on stale session state.
- The `screen` query parameter is only applied once per session, so a stale `?screen=question` URL no longer overrides the feedback screen after submission.
- The active question screen now uses the reference copy and sidebar values from the mockup.
- The feedback screen now renders the diagnostic card, score breakdown, strengths, weak points, improvement notes, and technical JSON breakdown from the feedback mock-up.
- The feedback screen now includes a working `Show Example Answer` button that opens the improved-answer learning reference screen.
- The feedback screen now surfaces trust level, score confidence, decision confidence, and reasoning depth before the score breakdown.
- The feedback screen now shows a follow-up learning card and keeps the reasoning assessment in a single block instead of repeating it.
- The feedback screen now adds a compact score-consistency note when the visible decision does not match the score-based verdict.
- The follow-up card now uses the weakest score, issue context, and reasoning depth to generate a more targeted next question when no follow-up is present.
- Strengths are now prioritised so the strongest signals appear first.
- The feedback screen now keeps all content inside the right-hand main panel and shows the technical JSON section expanded by default, matching the mock more closely.
- The evaluation pipeline now uses a model-assisted evidence extraction pass before scoring, then records contradiction flags and validation warnings in the returned payload.
- Answers with clear metrics are now evaluated against a structured evidence context with confidence scores, so missing-metrics feedback is less likely to be invented.
- The evaluation output now also surfaces anomaly flags for ambiguous, fake-looking, and non-impact numbers.
- Validation warnings now include severity, grouped anomaly flags, and a score confidence indicator.
- Validation warnings now also carry a trust level, reasoning depth, and dimension-level contradiction summary so the flags change how the result should be read.
- Validation output now separates validation, trust, and reasoning blocks, and includes `evaluation_version`, `evaluation_trace`, and `impact_strength`.
- The evaluation layer now includes a small internal calibration dataset to keep trust and reasoning checks deterministic.
- `overall_decision` remains the legacy visible decision, while `overall_decision_detail` carries decision confidence and trust gating context.
- Reasoning depth now uses `none`, `implicit`, `developing`, `explicit`, and `deep`, and anomaly influence is exposed as a machine-readable object.
- Score normalisation is available behind an explicit switch and remains disabled by default.
- The evaluation parser now accepts the prompt-contract JSON shape with `evaluation`, `summary`, `key_issues`, `improvements`, `reasoning`, `follow_up`, `topic_match`, `relevance_gate_applied`, and `trust`, while still supporting the legacy backend payload.
- Relevance is now short-circuited by a pre-classifier before the expensive LLM scoring path runs.
- The evaluation layer now grounds trust and decision details against evidence context before exposing them to the UI.
- The evaluation path now runs through an explicit controller with input validation, pre-classification, scoring, grounding, trust calculation, and grounded follow-up generation.
- The evaluation output now includes `evaluation_pipeline`, `grounding_score`, and `evaluation_confidence` so the stage order and confidence are visible.
- The evaluation output now also includes `failure_type` and a simplified `evaluation_summary` for the user-facing feedback screen.
- The feedback screen now shows a compact, read-only reliability card under Overall Outcome with confidence, grounding, and assessment labels.
- Follow-up questions are now re-grounded against the detected issue context before they are returned.
- When structured evaluation data is present, the question screen now routes to feedback instead of re-rendering the question view.
- If answer evaluation fails because the API key is invalid or the LLM is unavailable, the question screen now stays open and shows a friendly inline warning instead of crashing the app.
- The feedback screen also includes a JSON download for the current evaluation payload.
- The improved-answer screen now shows the original question, the submitted answer, and a stronger example answer side by side, with controls to return to feedback or continue to the next question.
- Submitting an answer now preserves the draft in session state and carries the question and answer into the feedback screen.
- The question submit button stays disabled until you type some text, then validation still blocks empty or too-short answers on submit.
- The Clear button now resets the answer box through the session-state callback.
- Starting the interview no longer triggers the Streamlit `Calling st.rerun() within a callback is a no-op` warning.
- Backend evaluation now expects structured evidence-first JSON with metrics, actions, reasoning, technical accuracy, clarity, structure, relevance, strengths, improvement areas, and an overall summary.
- Backend report download now produces a JSON session report payload for the summary flow.
- Backend session summary now aggregates scores, duration, strengths, and next steps to match the session summary mockup.

## Phase 1 provider configuration

The interview screens and session storage are unchanged. Administrators can set
`LLM_PROVIDER=ollama`, `OLLAMA_API_KEY`, `OLLAMA_MODEL=gemma4:cloud` and
`OLLAMA_HOST=https://ollama.com` in the application environment or private `.env`.
Restart Streamlit after changing settings. No local Ollama installation is needed.
Explicit `OLLAMA_HOST` and `OLLAMA_API_KEY` values in `.env` take precedence over
inherited Windows settings, so the app uses the project cloud address and key.

OpenRouter remains the default. Set `LLM_PROVIDER=open-router` to switch back.
Ollama failures reach OpenRouter only with `OLLAMA_FALLBACK_TO_OPENROUTER=true`
and an `OPENROUTER_API_KEY`. Cloud JSON is requested through prompts and validated
locally; it is not guaranteed by the model. Failed evaluations request a retry
without assigning scores. The API currently provides only `/api/health`;
Streamlit continues to call the existing services directly.

See [Phase 1 integration](phase1-integration.md) for setup and limitations.

## Direct Grok provider

Set `LLM_PROVIDER=grok`, `GROK_MODEL=grok-4.3` and a valid `XAI_API_KEY`
in the private application configuration, then restart Streamlit using the project
virtual environment. Grok calls go directly to xAI; OpenRouter and Ollama are not
used as automatic fallback providers. Existing interview screens remain unchanged.
An xAI API key and account access are separate from a Grok chat subscription.

## Direct Google Gemini provider

Set `LLM_PROVIDER=google`, `GOOGLE_MODEL=gemini-3.5-flash-lite` and a valid
`GOOGLE_API_KEY` in your private `.env`, then restart Streamlit. Create the key at
https://aistudio.google.com/apikey; never paste it into chat or commit it. The
selected model has free-tier input/output according to Google's current pricing,
subject to project eligibility and quotas. Your Google project's billing settings
determine the applicable tier. No fallback to another paid provider is enabled.
The existing screens, session management and evaluation checks remain in place.

## Question generation reliability

Gemini requests exactly five base questions covering the five interview categories
and capability dimensions. Partial responses are retried with a specific correction.
Existing question-count, relevance, scenario and duplicate checks remain active.
If neither model output nor existing backup candidates pass validation, the app
returns to setup with a retry error. It does not display invalid backup questions.

Without a CV or job description, questions use the selected role and do not assume
named tools or past candidate experience. Backup scenarios cover the same five
dimensions and must pass the same checks as model questions.

## Question relevance

Technical scenarios are assessed against the question you answered. Missing STAR,
personal examples or historical metrics do not make an answer off-topic. Uncertain
relevance produces provisional feedback; confirmed off-topic answers retain the
relevance gate. Follow-ups stay tied to the original question and submitted answer.

## Feedback reliability

Empty feedback lists stay empty. Unsupported claims and malformed example answers
are withheld. Technical scenarios do not require STAR or historical results.
Provisional evaluations do not store conclusions in future-session memory.
Feedback confidence and verdict confidence are displayed separately.

## Performance and assessment confidence

A provisional assessment keeps the score-based performance verdict. Confidence
and candidate performance are separate signals. Supported coaching stays visible
at low confidence; missing coaching receives one feedback-only repair attempt.
Follow-ups probe an actual answer decision without repeating the whole question.

## Phase 3A service limits

Interview requests now share a configurable deadline. Expiry shows a retry message
without recording scores. Quota-limited services ask you to wait. Screens and
session ownership remain unchanged. See [production readiness](phase3a-readiness.md).

## Cloud test preparation

See [Phase 3B proposal](phase3b-proposal.md) and [free Redis setup](phase3b-upstash-setup.md). Real Redis verification passed; Git publication and Preview deployment await approval.

## Dependency security update

The supported runtime pins have been patched; screens and interview behaviour are preserved. See [the security review](dependency-security-review.md) for tested versions and remaining release checks.

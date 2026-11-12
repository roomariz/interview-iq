**Interview-practice app**
This is a Streamlit interview-practice app with a layered frontend/backend design, OpenRouter-based model routing, evidence-first evaluation, and a fairly strong guardrail stack. The live question-generation path is mostly structured zero-shot prompting with hard constraints, not an explicit few-shot or chain-of-thought setup.

Use the repository root when running the app, especially on Windows. Avoid hardcoded `/mnt/d/...` paths in favour of relative links and commands such as `streamlit run app.py`.

**Repo Map**
- Root launcher: [app.py](../../app.py#L1)
- Streamlit entry point and startup: [interview_app_frontend/app.py](../../interview_app_frontend/app.py#L80)
- Frontend: [interview_app_frontend/](../../interview_app_frontend)
- Backend: [interview_app_backend/](../../interview_app_backend)
- Config: [config/](../../config)
- Shared types/constants: [shared/](../../shared)
- Product docs and mockups: [doc/](../)
- Tests: [tests/](../../tests)

**What You Are Using And Why**
- Streamlit for the UI because this is a single-user, stateful, multi-screen prototype that benefits from fast iteration and `st.session_state`.
- OpenRouter via the OpenAI client because it gives one API for multiple models and makes fallback routing easier. See [interview_app_backend/llm/client.py](../../interview_app_backend/llm/client.py#L45).
- Google and Grok clients as backup providers for resilience. See [interview_app_backend/llm/provider_clients.py](../../interview_app_backend/llm/provider_clients.py).
- Pydantic because the app depends on strict JSON output and schema validation for evaluation payloads. See [interview_app_backend/llm/parser.py](../../interview_app_backend/llm/parser.py).
- `fpdf2` because the summary/report flow supports PDF output as well as JSON. See [interview_app_backend/services/report_service.py](../../interview_app_backend/services/report_service.py#L54).
- `playwright` and `pytest` because the repo has UI and regression coverage.

**Main Features**
- Welcome, setup, question, locked-evaluation, feedback, sample-answer, and summary screens. See [interview_app_frontend/ui/screens.py](../../interview_app_frontend/ui/screens.py).
- Role, persona, difficulty, response style, CV, job description, temperature, and tech stack setup. See [interview_app_frontend/components/shell.py](../../interview_app_frontend/components/shell.py#L155).
- Background question generation with prepared question bundles, fallback recovery, and live model/provider metadata. See [interview_app_backend/services/question_generation_job.py](../../interview_app_backend/services/question_generation_job.py#L288).
- Adaptive question planning from role, CV, JD, previous questions, and feedback signals. See [interview_app_backend/services/question_sequence.py](../../interview_app_backend/services/question_sequence.py).
- Answer validation, prompt-injection blocking, and answer length checks. See [interview_app_backend/utils/validation.py](../../interview_app_backend/utils/validation.py#L4).
- Evidence-first answer evaluation, relevance gating, trust/grounding, and follow-up generation. See [interview_app_backend/services/evaluation_pipeline.py](../../interview_app_backend/services/evaluation_pipeline.py#L18).
- Evaluation feedback screen with score breakdown, trust callout, reliability card, JSON download, and technical JSON view. See [interview_app_frontend/components/feedback_screen.py](../../interview_app_frontend/components/feedback_screen.py#L87).
- Session summary with averages, strengths, improvements, focus areas, and next steps. See [interview_app_frontend/components/session_summary_screen.py](../../interview_app_frontend/components/session_summary_screen.py#L8).

**Prompt Strategy**
- Active question generation is a structured zero-shot prompt, not a classic few-shot prompt. The live wrapper is in [interview_app_backend/services/question_service.py](../../interview_app_backend/services/question_service.py#L1357) and it delegates to [interview_app_backend/llm/prompts/question_generation.py](../../interview_app_backend/llm/prompts/question_generation.py#L190).
- The generation prompt uses `PRIORITY_ORDER`, `QUESTION_PLAN`, `PREVIOUS_QUESTIONS`, explicit role/CV/JD grounding, and an output-only contract. See [question_generation.py](../../interview_app_backend/llm/prompts/question_generation.py#L212).
- Guardrails are very explicit: concrete scenario, no generic wording, no unsupported technologies, and mandatory self-checks. See [question_guardrails.py](../../interview_app_backend/llm/prompts/question_guardrails.py#L27).
- Evaluation uses a two-stage prompt flow: evidence extraction first, then JSON-only scoring. See [evaluation_service.py](../../interview_app_backend/services/evaluation_service.py#L33) and [evaluation_service.py](../../interview_app_backend/services/evaluation_service.py#L59).
- Example-answer, reference-answer, and semantic-similarity are separate prompt templates. See [interview.py](../../interview_app_backend/llm/prompts/interview.py#L3).
- Few-shot support exists as scaffolding in `question_service.py`, but the active question path does not use it. The live path is effectively zero-shot plus guardrails. That is the honest review answer.
- Chain-of-thought is not explicit. My inference from the prompts is that the app asks for reasoning, trade-offs, and evidence, but it does not ask the model to expose hidden step-by-step CoT.

**Model And Settings**
- The setup screen exposes a temperature slider, default `0.7`. See [shell.py](../../interview_app_frontend/components/shell.py#L195).
- The runtime model is controlled by `MODEL_NAME` in `.env`, and the app logs the resolved model at startup. See [interview_app_frontend/app.py](../../interview_app_frontend/app.py#L80).
- In this repo, the default is a free Google model chain, with `openai/gpt-5-nano` as a safety net. See [README.md](../../README.md#L19).
- That is a deliberate cost/reliability choice, but it is a deviation from the `115.md` recommendation, which asked for GPT-5 mini/nano/5. Be ready to explain that trade-off.

**Security Guards**
- Answer length validation and prompt-injection blocking. See [validation.py](../../interview_app_backend/utils/validation.py#L20).
- Relevance pre-classifier before deeper evaluation. See [evaluation_pipeline.py](../../interview_app_backend/services/evaluation_pipeline.py#L66).
- Hard relevance gate for off-topic answers. See [evaluation_pipeline.py](../../interview_app_backend/services/evaluation_pipeline.py#L111).
- JSON schema repair and validation on model output. See [interview_app_backend/llm/parser.py](../../interview_app_backend/llm/parser.py).
- Question-generation fallback validation, duplicate filtering, and hallucinated-tech checks. See [question_generation_job.py](../../interview_app_backend/services/question_generation_job.py#L318).
- These are the points to emphasise if a reviewer asks whether the app can be abused or can hallucinate freely.

**What From `115.md` Is Covered**
| Point | Level category | Note |
|---|---|---|
| Streamlit front end | Medium | Single-user multi-screen prototype built around Streamlit state. |
| OpenRouter integration | Medium | One API layer with provider fallback routing. |
| LLM settings tuning | Medium | Temperature is user-tunable. |
| Security guard | Medium | Input validation, prompt-injection blocking, and output checks. |
| Multiple prompt templates | Medium | Present, but the live path is mainly structured zero-shot. |
| Job-description and CV personalisation | Medium | Questions are grounded in user context. |
| Structured outputs | Hard | Evaluation and question bundles rely on strict JSON shaping. |
| Optional report output | Medium | JSON and PDF report paths exist in services. |
| Optional hard tasks like deployment, vector DB, image generation, and full chatbot behaviour | Hard | Not obviously implemented in this repo. |

Overall scope level: medium to hard, because the core interview loop, grounding, fallback routing, and evaluation pipeline are implemented, but the more advanced optional items are incomplete or absent.

**Review Talking Points**
- The startup path is now consistent: README says `streamlit run app.py`, and the root [app.py](../../app.py#L1) imports and calls [interview_app_frontend/app.py](../../interview_app_frontend/app.py#L80).
- `question_service.py` is large and mixes prompt building, validation, fallback, and bundle shaping. That is fine for a sprint project, but a reviewer may ask about maintainability.
- The free-model default is pragmatic, but it is not the exact model choice requested in `115.md`. Just be explicit about why.

**Verification**
- `python -m py_compile` passed on the key modules I checked.
- `pytest tests/test_request_log_panel.py -q` passed with `3 passed, 1 warning`.
- `pytest -s tests/test_request_log_panel.py -q` also passed with `3 passed, 1 warning`.
- The only warning is a `Styler.applymap` deprecation in `interview_app_frontend/components/request_log_panel.py`.

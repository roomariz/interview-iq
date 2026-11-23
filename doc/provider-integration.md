# Provider integration: FastAPI and Ollama Cloud

## Architecture

Streamlit still calls the existing backend services directly. Session management,
screens, relevance checks, grounding and feedback rendering remain in place.
FastAPI is an independent ASGI application exposing `GET /api/health`, returning
`{"status":"ok"}` without loading credentials or contacting an LLM.

The legacy service factory `get_openrouter_client()` now honours `LLM_PROVIDER`.
Ollama uses the documented HTTP API through the existing `requests` dependency:
`POST https://ollama.com/api/chat`, bearer authentication, non-streaming responses.
No local Ollama process or model download is needed. `create_openrouter_client()`
continues to create an OpenRouter SDK client directly.

Provider selection is separate from model ranking. `OPENROUTER_MODEL_NAME` retains
the original OpenRouter model; its free, question-generation and evaluation chains
are unchanged. `MODEL_NAME` identifies the selected provider's model for the
existing question prompt and session profiles. Ollama uses the existing strict
question profile, including its five-question session size.

Question output is checked against the existing question contract. Evidence and
scoring output pass through the existing Pydantic parsers. Plain-text relevance,
reference answers, similarity and example answers retain their existing formats.
The scoring evidence and relevance checks have not been bypassed.

The former evaluator failure path fabricated 5/10 scores. It now raises a friendly
error through the existing UI error flow, without recording placeholder scores.
Existing relevance-gate decisions for off-topic answers remain unchanged.

## Configuration

Install dependencies into your virtual environment:

```powershell
python -m pip install -r requirements-dev.txt
```

For Ollama, set these in the process environment or your private `.env`:

```ini
LLM_PROVIDER=ollama
OLLAMA_API_KEY=your_api_key
OLLAMA_MODEL=gemma4:cloud
OLLAMA_HOST=https://ollama.com
OLLAMA_FALLBACK_TO_OPENROUTER=false
LLM_TIMEOUT=60
```

OpenRouter is the default when `LLM_PROVIDER` is absent. `openrouter` and
`open-router` are accepted aliases. To switch back, set `LLM_PROVIDER=open-router`
and supply `OPENROUTER_API_KEY`. Existing `MODEL_NAME`, `IS_FREE_MODE` and model
ranking settings continue to govern OpenRouter requests.

Ollama requires no OpenRouter key unless fallback is enabled. To enable it:

```ini
OLLAMA_FALLBACK_TO_OPENROUTER=true
OPENROUTER_API_KEY=your_openrouter_key
```

Fallback is disabled by default, including in free mode. When enabled, exhausted
Ollama failures can use the original OpenRouter chain. Cancellation never triggers
fallback. Authentication and other permanent HTTP errors fail without retrying
Ollama; rate limits, timeouts, connection failures, server errors and invalid output
allow at most two Ollama attempts, with one second between attempts.
`LLM_TIMEOUT` applies to each HTTP attempt; existing service-level retries can make
more than one provider call. Host validation and disabled redirects prevent the
Ollama bearer token being forwarded to another host.

New provider settings prefer environment variables, except `OLLAMA_HOST` and
`OLLAMA_API_KEY`: non-empty project `.env` values override inherited addresses and
credentials. Environment-only deployments remain supported. Existing OpenRouter
model and timeout precedence is preserved. Restart the app after any configuration
change. Never commit `.env` or place keys in browser code.

Run each entry point independently:

```powershell
python -m uvicorn api.index:app --reload
streamlit run app.py
```

The health endpoint is at `http://127.0.0.1:8000/api/health`. Streamlit does not
call it. No Vercel deployment or project connection has been made.

## Compatibility limitations

- Ollama Cloud currently does **not** support schema-constrained structured
  outputs. Requests omit `format`; JSON is requested through prompts, then
  validated locally. JSON/schema failures retry or fail explicitly. This offers
  no server-side guarantee of valid JSON. See
  [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
- `gemma4:cloud` is mapped to `gemma4:31b` for direct cloud HTTP requests. Other
  `OLLAMA_MODEL` values pass through unchanged and must be valid direct API IDs.
  This follows the current [cloud model documentation](https://docs.ollama.com/cloud/models)
  and [authentication example](https://docs.ollama.com/cloud/api).
- No live provider request was made. Account access, quotas, model quality and
  availability remain unverified. Automated model responses are mocked.
- The OpenAI SDK pin was updated from 1.55.3 to 1.109.1: the former lacked the
  `responses.create` method already used by this repository. It remains an
  OpenRouter client, not a direct OpenAI integration. The existing evidence-call
  validation was also corrected to use the evidence schema rather than scoring.
- Some legacy evaluation request-log labels still say OpenRouter.
  Actual LLM call metadata and generated-question metadata identify Ollama.
- Vercel packaging, execution limits, secrets and frontend API wiring are deferred.
  Browser and live-provider acceptance tests were not run.

## Verification results

Verified with Python 3.12 and the pinned FastAPI, Pydantic, HTTPX and OpenAI SDK
dependencies in the existing project virtual environment:

- Focused API/provider/workflow/parsing/relevance checks: **76 passed**.
- Full offline suite, fixed `PYTHONHASHSEED=0`: **343 passed, 13 failed,
  11 deselected**. All 13 failing test IDs also fail in the original tracked
  repository under the same environment and seed: **298 passed, 14 failed,
  8 deselected**. The OpenRouter timeout regression now passes.
- Remaining failures cover stale logging/SDK assertions, question fallback
  validation, semantic-similarity expectations, sample-answer state and an
  order-sensitive UI worker test. The UI test passes in isolation. These remain
  outside this phase's changes; the full suite is not green.
- Ruff passes for every changed Python file. Repository-wide Ruff still reports
  **53 errors** outside these changed Python files.
- `pip check` passes; `git diff --check` passes. Every added or modified Markdown
  and Python file remains at or below 250 lines.

Reproduce focused checks (one terminal command):

```powershell
python -m pytest tests/test_fastapi_health.py tests/test_ollama_configuration.py tests/test_ollama_provider.py tests/test_ollama_workflows.py tests/test_evaluation_pipeline.py tests/test_environment_loading.py tests/test_evaluation_parser.py tests/test_evaluation_parser_repair.py tests/test_question_generation_contract.py tests/test_session_manager_relevance_gate.py -q
```

Default pytest runs exclude `live` and `e2e` tests. The session-wide socket guard
blocks external connections through background worker shutdown; loopback remains
available for Windows asyncio and in-process FastAPI tests. Baseline comparisons
used a temporary archive of `HEAD`, cleared provider credentials and the same
offline guard. No live paid API request was used.

## Files added or modified

| File | Purpose |
| --- | --- |
| `api/index.py` | Retained the existing untracked health endpoint; added return typing |
| `config/settings.py` | Provider, cloud model, key, host and opt-in fallback settings |
| `interview_app_backend/llm/client.py` | Provider dispatch, explicit fallback, evidence validation |
| `interview_app_backend/llm/client_support.py` | Extracted existing helpers; timeout/authentication classification |
| `interview_app_backend/llm/ollama_client.py` | Cloud HTTP transport, validation and bounded retries |
| `interview_app_backend/services/evaluation_pipeline.py` | Removed fabricated degraded scores |
| `interview_app_backend/services/pipeline_output.py` | Extracted unchanged output/trust formatting to respect file limits |
| `.env.example` | Provider configuration template |
| `requirements.txt` | Pinned FastAPI, HTTPX, Uvicorn and compatible OpenAI SDK |
| `requirements-dev.txt` | Pinned pytest and Ruff |
| `pytest.ini` | Excluded live and browser tests by default |
| `tests/conftest.py` | External-network guard |
| `tests/test_fastapi_health.py` | In-process health and route-scope tests |
| `tests/test_ollama_configuration.py` | Defaults, environment precedence and preserved ranking |
| `tests/test_ollama_provider.py` | Mocked transport, errors, switching, cancellation and fallback |
| `tests/test_ollama_workflows.py` | Existing question/evaluation/relevance and SDK compatibility workflows |
| `tests/test_evaluation_pipeline.py` | Replaced placeholder-score expectation with explicit failure |
| `tests/test_google_api_key.py` | Marked credential/live API checks as live-only |
| `doc/manual.md` | User configuration and failure behaviour |
| `doc/developer-manual.md` | Implementation and provider routing |
| `doc/test-manual.md` | Offline and manual verification steps |
| `doc/provider-integration.md` | Architecture, configuration, results and limitations |
| `AGENTS.md` | Recorded the user-defined Provider integration scope boundary |

## Follow-up: direct Google Gemini

The user subsequently selected direct Google Gemini instead of direct Grok.
The private project configuration now selects `LLM_PROVIDER=google` and
`GOOGLE_MODEL=gemini-3.5-flash-lite`. A valid `GOOGLE_API_KEY` must be supplied
privately before interviews can use Google; none was configured during this switch.
No API keys were changed and no live generation request was made.

The existing Google client now uses the documented OpenAI-compatible Chat
Completions URL. New `llm/google_chat.py` normalises completions for the existing
validation pipeline. New `tests/test_google_provider.py` covers configuration,
mocked HTTP, JSON validation, evaluation, rate limits, timeouts and failure paths.
`config/settings.py`, `llm/client.py`, `llm/client_support.py`,
`llm/provider_clients.py`, `.env.example` and the three manuals were updated.
`interview_app_frontend/app.py` now logs the actual selected provider and model.

Google lists this model with free-tier input/output, subject to account/project
eligibility and quotas. Model selection does not change the project's billing
tier. See [Google pricing](https://ai.google.dev/gemini-api/docs/pricing) and
[Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).

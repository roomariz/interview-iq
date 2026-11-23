# Streamlit and FastAPI integration

Implemented locally on 16 November 2026. No deployment, database, provider switch
or live provider smoke test was performed. Existing prompt text and score rules
are unchanged; some pure helpers moved into `shared/` with compatibility exports.

## Workflow analysis and contracts

| Existing workflow | HTTP backend separation boundary | Context and result |
| --- | --- | --- |
| `session_manager.start_interview` → inference and gap analysis | `POST /api/interview/context` | Role, optional CV/JD and requested question type → stack, competencies, gaps and safe provider profile |
| Backend question job → `get_next_question_for_session` | Frontend HTTP job → `POST /api/interview/question` → same service | Setup, index, previous questions/topics, competencies and gaps → validated questionnaire, distribution and provider metadata |
| Answer worker → `evaluate_submission` | `POST /api/interview/evaluate` → same pipeline | Current question and trimmed answer only → complete scores, trust, coaching, evidence and follow-up |
| `show_sample_answer` → `generate_example_answer` | `POST /api/interview/example-answer` | Submitted answer only → existing rewrite; existing free-mode restriction retained |
| Follow-up | Included in evaluation; rendered from session state | Existing deterministic decision probe; no second LLM call or endpoint |
| Adaptive questions | Updated competencies and question type passed with next question | Existing frontend adaptation and backend question selection remain |
| Summary and downloads | Local Streamlit computation | `build_session_summary_view` aggregates recorded answers; existing JSON downloads remain local |
| CV/JD input | Setup context and question requests only | Existing deterministic parsers; CV text stays in the current Streamlit session |

The current UI offers CV text; PDF upload/extraction is not implemented by the
existing screen. HTTP backend separation does not add a new upload workflow. The unused standalone
backend report service has a different legacy score shape and is not the summary
screen's dependency, so it was not exposed as a new API.

## API documentation

Interactive schemas: `http://127.0.0.1:8000/docs`; JSON: `/openapi.json`.
`GET /api/health` remains public and returns `{"status":"ok"}`.
All four interview operations require `Authorization: Bearer <server secret>`.

Shared Pydantic models live in `shared/api_contracts.py`. Unknown request fields
are rejected. Role is required, at most 300 characters; CV/JD each allow 20,000;
questions allow 6,000; answers require 50–2,000 trimmed characters. Temperature
is 0–1; index is 1–10; previous questions are bounded. Nested context is bounded
and instruction markers are rejected before services run.

Question requests must match the backend model profile's exact per-request count:
one for a routed free model, five for the current non-free profiles. Setup returns
both this count and the separate session limit (three/five). Existing strict
bundle validation, grounding, duplicate checks, retries and safe fallback remain
inside the question service. The API rejects empty/partial results. Evaluation
responses require all five dimensions and retain legacy score aliases and the
complete existing confidence/degraded-result fields. Invalid evaluation output
returns an error with no manufactured scores.

```json
{"role":"Backend Engineer","difficulty":"Medium","persona":"Friendly",
 "response_style":"Concise","question_index":1,"question_list_count":1,
 "previous_questions":[],"competencies":[],"gap_analysis":{}}
```

Send that JSON to `/api/interview/question` for a backend using a free model.
For evaluation, send `{"question":"...","answer":"..."}`. Answers must meet the
length constraint. Do not send the CV, entire session or provider settings there.

Successful operations return 200 JSON. Errors share this shape:

```json
{"error":{"code":"validation","message":"Please check the interview inputs and their lengths."}}
```

| Status | Meaning |
| --- | --- |
| 400 / 415 | Invalid declared size / unsupported content encoding |
| 401 | Missing or incorrect server secret |
| 413 | Request exceeds 128 KiB, including chunked requests |
| 422 | Invalid JSON, input, instruction markers or incompatible question count |
| 429 | Instance request budget exceeded; `Retry-After: 60` |
| 502 | Provider failure or invalid output; private exception details withheld |
| 503 | Missing backend secret, instance concurrency limit or provider busy |
| 504 | Provider timeout, including wrapped timeout causes |

## Local setup

Use the project's pinned virtual environment, not an unrelated system Python:

```powershell
.venv/Scripts/Activate.ps1
python -m pip install -r requirements-dev.txt
$env:BACKEND_API_SECRET = '<random shared server secret>'
python -m uvicorn api.index:app --reload --port 8000
```

In a second PowerShell terminal, activate the same environment:

```powershell
$env:BACKEND_API_SECRET = '<same random shared server secret>'
$env:BACKEND_API_URL = 'http://127.0.0.1:8000'
$env:BACKEND_API_TIMEOUT = '180'
python -m streamlit run app.py
```

The frontend also accepts these three settings from ignored
`.streamlit/secrets.toml`. Use a cryptographically random secret of at least 32
bytes. Backend provider keys remain in backend environment variables/private
`.env`; do not install them as Streamlit hosting secrets. The frontend no longer
imports provider settings or a provider SDK. Its shared code contains no keys.
The backend's dotenv loading supplies its own secret if configured in `.env`;
the frontend deliberately reads only process environment or Streamlit secrets.

Ollama configuration is preserved:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_API_KEY=your_api_key
OLLAMA_MODEL=gemma4:cloud
OLLAMA_HOST=https://ollama.com
OLLAMA_FALLBACK_TO_OPENROUTER=false
```

OpenRouter rankings and existing Google/xAI configurations are retained. No
automatic paid fallback was added. Changing providers still requires restarting
the backend. Restart the interview after changing the backend model profile.

## State, errors and security

FastAPI stores no interview sessions. Every operation receives its own context.
Streamlit owns futures, answers, feedback and adaptation; workers receive copied
payloads and a client configured on the script thread. Reset ignores stale work.
Mutable defaults are deep-copied so separate sessions cannot share answer lists.
Cancellation cannot undo an already-sent provider request; the frontend does not
automatically retry POSTs, to avoid duplicate model calls.

The client validates responses, blocks redirects, requires HTTPS for remote
backends and maps errors to frontend-owned messages. It logs neither payloads
nor server error bodies. API failures omit prompts, credentials and input values.
Interview responses carry `Cache-Control: no-store`. No CV/answer files are written.

CORS is disabled: no browser origins are granted cross-origin response access.
Authentication is the independent bearer-secret check. Browsers never need the
secret because Streamlit sends requests from its server process.

Defaults: 30 authenticated requests/minute and four concurrent requests per
backend worker, controlled by `BACKEND_RATE_LIMIT` and `BACKEND_MAX_CONCURRENT`.
These counters contain no session data. They reset on restart and do not span
multiple workers or instances. A shared frontend secret does not identify users.
Production ingress budgets, per-user controls, secret rotation, monitoring and
distributed rate limiting require Phase 3 infrastructure.

## Vercel compatibility review

The stateless ASGI app fits the supported Python/FastAPI runtime. Actual deployment
packaging and routing have not been tested. Choose the API entrypoint explicitly:
this repository also contains a root Streamlit `app.py`.
[Python runtime documentation](https://vercel.com/docs/functions/runtimes/python).

Vercel currently documents a 4.5 MB request/response cap, a standard 500 MB Python
bundle limit, and Fluid Compute durations starting at 300 seconds. Limits depend
on plan and enabled features; verify them during Phase 3.
[Function limits](https://vercel.com/docs/functions/limitations).

Our request cap is 128 KiB; frontend responses are limited to 1 MiB. Typical
mocked questionnaires/evaluations fit these bounds. Actual maximum provider output
and the Linux deployment bundle have not been measured. Root requirements include
Streamlit, Playwright, pandas and test tooling: prepare backend-only dependency
packaging and exclude virtual environments, tests, docs and local secrets.

Provider timeouts remain 60 seconds per configured attempt by default; Ollama
permits two attempts and services can retry. Evaluation can make several sequential
calls for relevance, reference/similarity, evidence, scoring and coaching repair.
The existing 12-second LLM retry budget checks between calls, not a hard deadline
around each operation. Worst-case elapsed time can exceed the frontend's default
180-second timeout or a hosting duration. This is a deployment blocker until
aggregate deadlines and measured provider latency are agreed. Do not solve it by
fabricating scores or silently changing model rankings.

API code uses no temporary CV files or backend session threads. Production env
must contain only backend provider keys and the shared secret. Before Phase 3,
resolve existing test failures, measure bundle size/latency, configure aggregate
timeouts, distributed abuse controls, HTTPS and secret rotation, then seek explicit
deployment approval. See [test results](http-backend-test-results.md) and
[created/modified files](http-backend-file-inventory.md).

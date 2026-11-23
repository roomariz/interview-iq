# Backend production readiness

Implemented locally only. Streamlit, API schemas, scoring, prompt text and provider
rankings are preserved. No deployment, shared service creation or live LLM call
was performed. See [verification](backend-readiness-test-results.md) and
[file inventory](backend-readiness-file-inventory.md).

## Assessment and request lifecycle

HTTP backend separation reset provider timeouts between operations and used instance-local quotas.
The deployed backend now has an aggregate deadline and requires shared quotas.
Production dependency imports and startup work independently of the frontend.
Deployment readiness remains conditional on the Protected Preview build and service checks
below; a local test cannot establish hosted routing or actual provider latency.

Question generation can nest service correction attempts, provider retries and
ranked model fallback. Evaluation can call relevance, reference generation,
similarity, evidence extraction, scoring and coaching repair sequentially.
Structured JSON validation remains at the transport and service boundaries.
Adaptive questioning uses the same question route; follow-ups remain deterministic.
CV/JD parsing and gap analysis are deterministic and use no additional model calls.

## Deadline and retry design

`BACKEND_REQUEST_DEADLINE` defaults to 150 seconds, including shared-quota lookup,
request-body reading, thread-pool queueing, service work and response production.
The allowed range is greater than zero and at most 270 seconds, leaving headroom
under the prepared 300-second function duration. The frontend defaults to 180
seconds: keep its timeout above the chosen backend deadline plus network overhead.

A ContextVar carries a single monotonic expiry and cancellation Event into FastAPI
workers and transport threads. Each provider call receives the lesser of
`LLM_TIMEOUT` and remaining request time. A separate wall-clock wait covers slow
or trickling transports whose socket timeout alone is insufficient. OpenAI SDK
automatic retries are disabled; existing explicit model/provider/service attempt
limits remain. Backoff waits consume the same remaining budget. No validation
steps, scores or prompts were removed to reduce latency.

Expiry produces the existing sanitised HTTP 504 contract. Route completion checks
the budget again, so a service that catches an intermediate error cannot return
scores after expiry. Nested retries check before starting new calls. End-of-request
cancellation prevents abandoned workers from starting more model work.

Python cannot forcibly kill a synchronous HTTP operation already in progress.
Its daemon transport thread retains one of 16 process-local slots until exit;
new operations fail when slots are exhausted. Socket timeouts still apply.
An already-sent provider request may incur a charge even after HTTP cancellation.
The legacy 12-second retry-loop guard remains; it is not the aggregate deadline.
Direct service calls outside HTTP retain their existing local timing behaviour.

## Distributed rate limiting

Production uses Upstash-compatible Redis REST via existing httpx, with no extra
SDK or interview database. One EVAL script atomically increments a counter and
sets/reads its 60-second expiry using server time. Independent instances with the
same namespace and authenticated secret share the quota. Requests over the limit
return 429 and a rounded-up Retry-After. Invalid authentication returns 401 before
quota access; it cannot consume the legitimate quota or invoke a model.

The key contains a SHA-256 digest of the configured server secret, never a user
identifier, CV, answer or forwarded IP header. This is a shared server-wide budget,
not per-user identity. Rotating the secret creates a new counter. Fixed windows
allow a boundary burst up to twice the limit. Every authenticated request attempt
consumes quota, including invalid input or an instance-busy response.

Timeouts, HTTP failures, invalid Redis results and missing configuration fail
closed with 503; there is no production fallback to in-memory quotas.
`BACKEND_MAX_CONCURRENT` remains a per-instance work cap; Redis quotas provide the
cross-instance request admission budget. Unauthenticated ingress abuse still needs
hosting firewall controls; user-level quotas require authenticated user identity.
Protocol: [Upstash REST](https://upstash.com/docs/redis/features/restapi) and
[EVAL](https://upstash.com/docs/redis/sdks/py/commands/scripts/eval).

## Configuration

| Setting | Local / test | Production |
| --- | --- | --- |
| APP_ENV | local / test | production (default on Vercel) |
| BACKEND_RATE_BACKEND | memory or redis | redis required |
| BACKEND_API_SECRET | shared with Streamlit | at least 32 bytes; generate randomly |
| BACKEND_RATE_LIMIT | 30/minute default | same shared quota across instances |
| BACKEND_MAX_CONCURRENT | 4 default | 4 per instance default |
| BACKEND_REQUEST_DEADLINE | 150 seconds default | positive, at most 270 seconds |
| BACKEND_RATE_NAMESPACE | interviewiq default | separate preview/production namespaces |
| UPSTASH_REDIS_REST_URL | required only for redis | required HTTPS URL |
| UPSTASH_REDIS_REST_TOKEN | required only for redis | required write-capable secret token |

Test and production modes ignore repository `.env` files. Local mode retains
existing dotenv precedence. Limits and required secrets are validated at the
interview request boundary; public health remains liveness, not provider readiness.
Production requires the selected provider's key and a positive LLM timeout.
Explicit Ollama fallback additionally requires its OpenRouter key. Existing
`LLM_PROVIDER`, model, host and fallback settings remain configurable. No new
automatic paid fallback or hardcoded production backend URL was introduced.

## Backend packaging and Vercel assessment

`requirements-backend.txt` contains backend runtime and security transitive pins;
`requirements-frontend.txt` supports Streamlit separately. Existing root/local and
development requirements remain available. `pyproject.toml` repeats the backend
pins for Vercel's manifest discovery and declares Python 3.12 and
`tool.vercel.entrypoint = "api.index:app"`. Keep the two backend pin sets aligned.
This explicit entrypoint avoids the root Streamlit `app.py`.

The active Google client uses OpenAI-compatible chat, so the optional legacy
google-generativeai SDK is unnecessary for API execution. Text CV processing uses
standard-library code. PDF upload is not implemented; the unused legacy PDF report
service is outside the API and does not require fpdf/pandas in the function.
Vercel exclusions omit frontend, tests, docs, environments and local secrets.

Reviewed current official documentation on 16 November 2026:

| Concern | Finding / prepared configuration |
| --- | --- |
| Runtime | Python 3.12 supported; pyproject restricts this backend to 3.12 |
| Entrypoint | Explicit custom FastAPI entrypoint supported; one ASGI application |
| Duration | Fluid Hobby default/maximum 300s; prepared maxDuration 300, app default 150 |
| Payload | Platform request/response cap 4.5 MB; API input cap 128 KiB, frontend response cap 1 MiB |
| Packaging | Standard uncompressed Python bundle cap 500 MB; no Python tree-shaking |
| Filesystem | Read-only except ephemeral /tmp; API writes no CV/session files |
| State | Streamlit owns sessions; Redis contains expiring quota counters only |
| Connectivity | Outbound HTTPS needed for provider and Redis; verify region/egress during preview |
| Concurrency | Context-isolated budgets, atomic shared quotas, bounded per-instance work |
| Secrets | Backend provider keys and Redis token stay server-side; no CORS grant or browser secret |

Sources: [Python runtime](https://vercel.com/docs/functions/runtimes/python),
[FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[limits](https://vercel.com/docs/functions/limitations),
[filesystem](https://vercel.com/docs/functions/runtimes),
[environment variables](https://vercel.com/docs/environment-variables).

Linux CPython 3.12 binary dependency resolution succeeded: 24 wheels, 16,910,856
uncompressed bytes (16.13 MiB). This excludes the runtime, application source,
generated bytecode and Vercel packaging overhead. The actual deployed bundle has
not been built or measured. Oversized provider responses could exceed hosting
limits; existing frontend validation rejects responses above 1 MiB. Real output
sizes and latency must be measured before launch. See verification for baseline
test failures that still require separate resolution.

## Proposed Protected Preview instructions — not executed

1. Review these changes and the retained baseline failures; explicitly authorise
   resource creation and deployment before any external mutation.
2. Provision/select a Redis REST database. Use one namespace across production
   instances, a separate preview namespace, and a write-capable server-only token.
3. Configure Vercel Python 3.12, FastAPI framework and this repository's explicit
   entrypoint. Verify Fluid Compute and maxDuration 300 in the selected plan.
   Inspect build logs to confirm only pyproject backend dependencies are installed.
4. Set APP_ENV=production, BACKEND_RATE_BACKEND=redis, the Redis URL/token, a random
   shared secret, selected provider settings and the aggregate deadline. Do not
   upload `.env`, frontend secrets or personal test inputs.
5. Run the Linux/Vercel build; inspect the complete function bundle and exclusions.
   Stop if frontend dependencies, secrets or an incorrect root entrypoint appear.
6. After deployment approval, create a protected preview and verify health,
   authentication, size rejection, combined quotas across instances and fail-closed
   Redis outages. Use provider mocks for the full interview workflow first.
7. Obtain explicit permission before live model checks; measure worst-case latency,
   payload sizes, cold starts and concurrent requests, including provider failures.
8. Configure Streamlit separately with only its backend URL, shared secret and a
   client timeout above the backend deadline. Require HTTPS for remote access.
9. Review logs for privacy, set provider spending caps/firewall controls, and approve
   production promotion separately. Preserve a rollback target and rotate secrets
   if exposed. No deployment command has been run during Backend readiness.

Security pins were updated on 17 November 2026; see [current remediation and validation](dependency-security-review.md). The original assessment above records the earlier phase results.

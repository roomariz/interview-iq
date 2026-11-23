# Final local deployment readiness — 17 November 2026

Recommendation: ready for reviewed GitHub publication and a protected, mocked
Vercel Preview after separate authorisation. Public production release is not
established. The earlier Redis anomaly remains unexplained; repeated passes do
not erase that uncertainty. No push, deployment, paid service or live LLM call ran.

## A. Git and scope

- Branch: `feat/streamlit-vercel-backend`.
- Previous commit: `014f06b80d5ff10f485cd412965c8f49771d58a1`, preserved unchanged.
- New local commit: the commit containing this report; obtain its exact hash with
  `git log -1 --format=%H -- doc/final-deployment-readiness.md`. The completion
  response records that hash and the final working-tree status.
- Commit message: `test: resolve baseline failures and assess deployment readiness`.
  “Assess” deliberately preserves the unresolved historical Redis uncertainty.
- Reviewed pre-existing work: four documentation edits, this report,
  `doc/test-failure-assessment.md` and five current-contract checks in
  `tests/test_readiness_current_contracts.py`. All are relevant and retained/updated.
- Additional scope: nine existing test modules corrected; feedback flow tests
  moved to `tests/test_feedback_screen_flow.py` to meet the 250-line rule;
  `tests/test_readiness_rate_limit.py` adds three cases; the Redis verification
  script gains diagnostics, invalid-token and expiry checks; AGENTS records scope.
- Documentation: `doc/manual.md`, `doc/developer-manual.md`, `doc/test-manual.md`
  and `doc/protected-preview-proposal.md` link to/currently reflect this assessment.
- Only source tests, the verification script and documentation are committed.
  Dotenv, caches, environments, audit JSON and smoke scripts remain ignored.
  No application modules, manifests, API contracts, prompts or rankings changed.

## B. Test results and baseline disposition

Complete run: **607 passed, 0 failed, 0 skipped, 11 deselected**, five warnings,
44.70 seconds. The established baseline was 592 passed/12 failed/11 deselected.
Twelve reconciled failures plus three new Redis HTTP-error cases explain 607.
The five previously uncommitted current-contract checks are included and pass.

[Individual assessment and correction of every baseline failure](test-failure-assessment.md)
contains the original identities, affected deployed paths, causes and assertions.
Summary: two logging expectations, scoring-call selection, three follow-up
expectations/fixtures, timeout/client configuration, SDK exception construction,
raw coaching provenance, bounded feedback repair and trusted memory fixtures.
All were outdated fixtures/assertions; no runtime defect was demonstrated.
Assertions now check verified contracts; no skip, xfail or suppression was added.

Passing suite coverage includes health and four interview endpoints, invalid/missing
backend authentication, authenticated HTTP Streamlit integration, independent
session state, mocked questions/evaluations, adaptation, summaries, Ollama and
OpenRouter selection/fallback, bounded retries/deadlines and fail-closed quotas.
The three new cases require sanitised 503 and Retry-After for Redis 401/403/500.
They passed again after the final fixture lint correction (3 passed, 2.38 seconds).

Reproduce with dummy keys, `APP_ENV=test`, `LLM_PROVIDER=open-router`:
`python -m pytest tests -q --tb=short --show-capture=no`.
External networking is blocked by the test fixture. Windows sandbox loopback
checks stalled; those runs were stopped and excluded. The successful run used
normal local loopback access. Eleven live/browser-marked tests were deselected,
not passed. Five existing dependency/styling deprecation warnings remain visible.

## C. Redis reliability

The earlier log records only `AssertionError`; its failed assertion, statuses,
TTL, timing and upstream response were not retained. Review cannot establish
whether timing, connectivity, isolation or configuration caused it. It is not
claimed resolved. Existing verification already used UUID namespaces, so shared
state is not demonstrated as its cause. No production limiter change was justified.

Two fresh-namespace real Upstash runs passed in this review:

| Check | Observed result in each completed run |
| --- | --- |
| Independent backend processes | Two Uvicorn processes, same namespace and temporary bearer secret |
| Atomic combined quota | Eight concurrent context requests: four 200 and four 429 |
| Backend authentication | Missing bearer rejected with 401 before consuming quota |
| Retry-After | Numeric 1–60 seconds on all quota rejections |
| Invalid Redis credentials | Separate backend returned sanitised 503 |
| Simulated Redis outage | Separate backend returned 503, no memory fallback |
| Quota expiry/reset | Context accepted with 200 after waiting beyond observed quota use plus 61 seconds |
| Privacy | Redis token/backend secret absent from tested response bodies |
| Inference | None; synthetic context requests only |

The newly added expiry assertion initially returned 429 because its wait was
measured from process startup, before quota creation. This test-harness timing
error was corrected to measure from completion of quota requests. It does not
explain the older anomaly, whose harness had no expiry assertion.

The unchanged Lua EVAL atomically increments and applies a 60,000 ms expiry,
using Redis TTL rather than the backend clock. Rejected requests increment the
counter but do not extend the window. Only unique `iqverify-<uuid>` keys were
written; all expire naturally, including reset keys. No unrelated Redis data was
read/deleted. All completed verification backends were stopped. Safe assertion
messages now retain statuses/check names without upstream bodies or credentials.

Residual risk: intermittent service/network failure, hosted latency, regional
connectivity and sustained load remain unmeasured. Fail-closed 503 protects quotas
but can reduce availability. Repeat on Preview and retain safe failure diagnostics.

## D. Anonymous-user quotas and abuse protection

Redis identity is `namespace:authenticated:sha256(BACKEND_API_SECRET)`.
The frontend sends one server-side credential; it sends no visitor/session identity.
IP, forwarded headers and user-supplied identifiers do not select quota keys.
Separate Streamlit visitors therefore share one allowance and can exhaust each
other's access. Separate namespaces or credentials create separate counters.

`BACKEND_RATE_LIMIT=30` allows 30 authenticated interview HTTP requests in the
60-second fixed window beginning at the first Redis increment. It includes context,
questions, evaluation and example-answer requests, not just inference; rejected
or invalid authenticated requests can consume quota. Health/unauthenticated
requests do not. One evaluation can invoke several bounded provider operations,
so 30 requests does not mean 30 LLM calls or a daily spending cap. Local memory
mode instead uses a process-local sliding 60-second window and is forbidden in
production/Vercel.

`BACKEND_MAX_CONCURRENT=4` is the middleware's in-memory active counter per
application process, not a distributed semaphore. More Vercel processes increase
total simultaneous work; Redis admission remains shared. Restarting an anonymous
Streamlit session/changing IP or headers does not reset the shared Redis quota.
A visitor can still consume it repeatedly each minute through the public frontend.
A leaked backend credential permits direct access subject to the same quota.
Authentication, deadlines, bounded retries and quotas reduce abuse but provide
neither fair visitor allowances nor a hard provider budget/global concurrency cap.

Simplest initial protected configuration: keep one Redis namespace/strong shared
secret, `APP_ENV=production`, Redis fail-closed, rate 30/minute and per-process
concurrency four; 150-second aggregate deadline and Ollama-only provider with
automatic OpenRouter fallback disabled. Keep keys server-side and Preview protected.
Before a public launch, set provider-side spending limits where supported, restrict
ingress and agree traffic/budget expectations; no numeric safe public capacity can
be inferred without usage data. Retain the global quota as a cost guard.

For public fairness, anonymous session quotas plus a shared application quota are
a reasonable next design. A server-issued session identifier would still be
resettable and must not replace the global guard. Daily quotas/global concurrency
could bound exposure further. These change identity/semantics and need approval;
none were implemented in this task. No login or database was introduced.

## E. Security and dependencies

| Check | Result |
| --- | --- |
| Runtime manifest audit (backend + frontend) | 49 resolved packages, zero known findings, zero skips |
| Development manifest audit | 82 resolved packages, zero known findings, zero skips |
| Installed `.venv` audit | 96 packages, zero known findings, zero skips |
| pip compatibility | Main, backend-only and frontend-only environments pass `pip check` |
| Changed-file Ruff | Zero findings |
| Repository Ruff | 35 existing findings remain (42 baseline; seven removed in touched test imports/bindings) |
| Secret scan | 302 tracked/untracked non-ignored candidates; zero configured-secret/token/private-key-pattern findings |
| Diff/artefacts | Whitespace clean; all changed Markdown/Python files within 250 lines |

Audits were repeated against current PyPI advisory data using isolated audit tools;
initial sandbox DNS failures were not counted as passes. No advisories were
suppressed. Audit outputs are ignored under `.pytest_cache/remediation-*-audit.json`.
A point-in-time scan cannot prove absence of every secret or undisclosed vulnerability.
No secret values were printed; response privacy, logging and sanitised errors are
covered by tests. Existing lint debt remains a maintenance issue, not a green
repository-wide lint gate. Dependency pins/security commit were not recreated.

## F. Packaging, Vercel and next gates

Backend and frontend manifests were reinstalled in their separate existing isolated
environments (pins already satisfied), then compatibility/startup checks passed.
Backend-only import/TestClient startup passes health, all four unauthenticated
rejections and authenticated context; Streamlit/Pillow absent. Frontend-only
AppTest welcome render, pandas styling compatibility and headless Streamlit health
pass; FastAPI/OpenAI absent. These are local checks, not a hosted certification.

Official documentation checked on 17 November 2026:

- [FastAPI framework](https://vercel.com/docs/frameworks/backend/fastapi): custom
  `tool.vercel.entrypoint` selects the application; FastAPI routes use one function.
- [Python runtime](https://vercel.com/docs/functions/runtimes/python): Python 3.12
  is supported; pyproject dependencies and explicit exclusions are supported;
  Python is not tree-shaken and the standard bundle limit is 500 MB uncompressed.
- [Function duration](https://vercel.com/docs/functions/configuring-functions/duration):
  Hobby with Fluid compute permits 300 seconds, matching `api/index.py` maxDuration.

Repository settings align: Python >=3.12,<3.13, `api.index:app`, FastAPI preset,
Frankfurt `fra1`, 300-second function setting, backend manifest/pyproject agreement,
frontend/development exclusions and automatic Git deployment disabled. No special
build/install/output override is proposed. The upgraded dependencies pass local
checks; actual Linux dependency resolution, discovered bundle contents/size,
entrypoint, region availability and project-plan settings still require a build.
No deployed routing, hosted Redis, cold-start or inference quality/cost claim is made.

Next, after explicit publication/deployment approval:

1. Publish only the reviewed feature-branch commit; preserve the existing public
   repository and avoid main merge/force-push. No publication occurred here.
2. Configure the protected Preview with environment-only Redis/backend/provider
   secrets, production controls and the reviewed Frankfurt configuration on the
   existing free plan. Confirm protection and disabled automatic Git deployments.
3. Check actual Linux build, bundle size/exclusions, function duration and routing.
4. Repeat hosted health/authentication/quota/expiry/outage checks and isolated
   mocked workflows; monitor sanitised failures for the unresolved Redis anomaly.
5. Obtain separate authorisation for live inference and any public quota/identity
   redesign. Production readiness remains conditional on those hosted and abuse gates.

# Anonymous access controls verification

17 November 2026. All provider responses mocked; no live inference or cloud change.

| Check | Result |
| --- | --- |
| Full automated suite, including real Redis | 636 passed; 11 live/e2e tests deselected |
| Real Redis subset | Five tests passed against Redis 8.10.2 core server |
| Cross-process concurrency | 12 simultaneous HTTP requests across two independent Uvicorn processes: two admitted, ten 429 at configured capacity two |
| Visitor quotas | Independent visitors; minute/day exhaustion; retry information |
| Global quotas | Combined minute/day exhaustion; fresh visitor cannot bypass global allowance |
| Atomic non-debiting rejection | Busy/quota denial leaves the denied visitor's counters unchanged |
| Identity | Randomness, isolation, stable server-session token, tampering, wrong key, expiry, future time and malformed/missing tokens |
| Authentication | Invalid bearer rejected before Redis; legacy authenticated contracts preserved |
| Redis failures | Outage, HTTP error and malformed response fail closed; no local fallback |
| Leases | Owner-only release/renewal, expiry/reset, stale release cannot remove successor |
| Timeouts | HTTP 504; retained lease while synchronous mock transport remains alive; release after it exits |
| Renewal failure | Invalid/lost lease and Redis outage cancel further deadline-aware work |
| Invalid payload | Schema-invalid JSON does not consume admitted-work allowances |
| Logging | HTTPX/HTTPCore/OpenAI/app/LLM event payloads, infrastructure URL, bearer, CV and exception text withheld; numeric status/duration retained |
| Runtime manifest audit | 49 packages; zero known vulnerabilities |
| Development manifest audit | 82 packages; zero known vulnerabilities |
| Installed environment audit | 96 packages; zero known vulnerabilities |
| Dependency compatibility | `pip check`: no broken requirements |
| Changed/new Python lint | Passed |
| Whole-repository lint | 35 findings in unchanged files; not modified as part of Anonymous access controls |
| Gitleaks source candidates and Git history | Zero findings, with redaction enabled |
| Git whitespace and touched-file size checks | Passed; all changed/created files at most 250 lines |

The suite emits five existing deprecation/future warnings from Starlette's HTTPX
test client, AnyIO, WebSockets and pandas styling. They were not suppressed.
Two legacy fallback tests now require redacted exception text; their UI/fallback
assertions remain intact. Log categories for timeout and JSON repair are retained.

## Reproduce without providers

Use Python 3.12 and the existing development environment. In PowerShell:

```powershell
$env:APP_ENV = 'test'
$env:LLM_PROVIDER = 'open-router'
Remove-Item Env:TEST_REDIS_PORT -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pytest -q --tb=short
```

The five real Redis tests skip unless `TEST_REDIS_PORT` is explicitly set.
To include them, start a **local, disposable, loopback-only Redis** with persistence
disabled; set `$env:TEST_REDIS_PORT='16389'` to its actual port and rerun the suite.
Use a real Redis server supporting EVAL/TIME/sorted sets. No Redis Python package
or other application dependency is required.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_distributed_admission_real_redis.py -q
.venv/Scripts/python.exe -m pytest tests/test_anonymous_identity_logging.py tests/test_distributed_admission.py -q
.venv/Scripts/python.exe -m ruff check api shared/visitor_identity.py
.venv/Scripts/python.exe -m pip check
```

This run compiled the official Redis stable source's core server in temporary WSL
storage. Optional module builds were unavailable and were not used. Redis ran in
the foreground on loopback with snapshots/AOF disabled. The test-only adapter sends
the actual production Lua over Redis's wire protocol; the independent backend
processes use the same middleware/admission implementation. The adapter is enabled
only in the synthetic test entrypoint, never in deployment code. It substitutes
for Upstash REST transport, so it does not prove hosted Upstash/Vercel behaviour.
Existing REST transport failure tests and new admission failure tests run offline.
The managed Redis script was updated for signed visitor headers but was not run
against cloud infrastructure during Anonymous access controls.

Windows asyncio requires loopback access. Sandbox runs stalled; the successful
suite used local loopback access with the existing external-network test guard
still active. Child processes receive only synthetic settings and no provider keys.
The simultaneous dispatch test uses one prepared async client so client startup
latency cannot accidentally produce sequential request batches.

Local audit/scan/test outputs and build material are ignored under
`.phase4a-local/`. The temporary server is stopped after verification. No generated
dependency, executable, audit inventory or secret is intended for Git publication.

## Manual protected-Preview checks after approval

Follow [the Preview proposal](anonymous-access-preview-proposal.md). With synthetic context only,
complete setup, question generation, evaluation, follow-up, example answer and
summary. Confirm unchanged screens/scores, two separate session identities and
friendly limit/retry errors. Reuse the same identity across requests and workers;
reconnect to confirm a new anonymous identity cannot bypass the global caps.
Inspect response bodies and normal runtime logs privately for sensitive values.
Do not contact a real provider or modify the inert Production bootstrap.

The local tests do not prove public abuse resistance, hard model-call/spending
budgets, cancellation of remote inference or live Ollama latency. Keep protection
enabled and use the permanent mock artifact for the next approved verification.

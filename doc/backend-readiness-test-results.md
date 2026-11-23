# Backend readiness verification results

## Results

| Check | Result |
| --- | --- |
| Isolated HTTP backend separation baseline | 554 passed, 12 failed, 11 deselected |
| Final full suite | 582 passed, 12 failed, 11 deselected |
| New Backend readiness tests | 28 passed |
| New failing identities versus baseline | None |
| Existing API, LLM integration and HTTP workflow checks | 30 passed |
| Changed/new Python files: Ruff | Passed |
| Git whitespace check | Passed |
| Modified/new source and documentation size | At most 250 lines per file |
| Fresh backend-only install, production imports, health and auth | Passed |
| Fresh environment pip check | No broken requirements |
| Linux CPython 3.12 binary dependency resolution | 24 wheels, 16.13 MiB uncompressed |
| Deployment / actual Redis / live provider calls | Not performed |

The baseline was copied from the existing HTTP backend separation index into ignored
`.pytest_cache/phase3-baseline/`; no source was reverted. JUnit failure identities
were compared, not just totals. The final run took 34.39 seconds and reported one
existing warning. All 12 failures listed in [HTTP backend separation results](http-backend-test-results.md)
remain; no existing test assertions were modified. This is not a fully green suite.

Initial sandboxed attempts stalled on Windows loopback operations. Completed API
and full-suite runs used local loopback permission with the existing external
network guard enabled. Temporary test-double compatibility failures found during
development were corrected in implementation, without changing existing tests.

## What was tested

- One budget across nested operations, slow/trickling provider wall time, exhausted
  backoff, cancellation, bounded explicit retries and disabled hidden SDK retries.
- Controlled API 504 and prevention of subsequent work by an abandoned worker.
- Ollama expiry prevents fallback; explicitly configured fallback inherits remaining
  time; independent asynchronous contexts retain separate budgets.
- Two independent FastAPI applications sharing one mocked Redis REST service:
  combined simultaneous quota, atomic EVAL request shape and Retry-After values.
- Invalid authentication and spoofed identifier headers cannot choose another quota.
- Redis outages and malformed responses fail closed; local in-memory quotas work.
- Production rejects local controls, weak secrets, invalid limits and Redis config.
  Vercel cannot select local mode. Test/production settings never read dotenv files.
- Backend requirements and Vercel pyproject dependency pins are identical.
- Existing authenticated contracts, structured question generation, evaluation,
  follow-up/adaptation, session summary and local Streamlit rendering remain covered
  by the full suite, using synthetic input and mocked providers.

The shared-service tests emulate REST replies; they do not execute Lua on a live
Redis service or prove hosted multi-instance behaviour. The atomic script uses
the documented Redis EVAL/INCR/PEXPIRE/PTTL semantics. Confirm the real service,
permissions, TTLs and failure behaviour in an authorised Protected Preview preview.

## Reproduce

```powershell
$env:APP_ENV = 'test'
$env:LLM_PROVIDER = 'open-router'
$env:OPENROUTER_API_KEY = 'local-test-key'
$env:GOOGLE_API_KEY = 'local-test-key'
$env:XAI_API_KEY = 'local-test-key'
.venv/Scripts/python.exe -m pytest -q --tb=short
.venv/Scripts/python.exe -m pytest tests/test_backend_deadlines.py tests/test_shared_rate_limits.py -q
```

The suite's external-network fixture blocks non-loopback sockets. Use the project
environment, not an unrelated system Python. For standalone backend verification:

```powershell
python -m venv .pytest_cache/backend-env
.pytest_cache/backend-env/Scripts/python.exe -m pip install -r requirements-backend.txt
.pytest_cache/backend-env/Scripts/python.exe -m pip check
```

The clean environment was configured with APP_ENV=production, dummy provider and
Redis keys, a dummy secret longer than 32 bytes, and a synthetic HTTPS Redis URL.
It imported `api.index:app`, validated production config and returned 200 for
health and 401 for unauthenticated interview requests through TestClient.
Streamlit and pandas were confirmed absent. No Redis/provider request is required
for these checks. Linux dependency inspection used:

```powershell
.pytest_cache/backend-env/Scripts/python.exe -m pip download -r requirements-backend.txt --platform manylinux2014_x86_64 --python-version 312 --implementation cp --abi cp312 --only-binary=:all: --dest .pytest_cache/backend-linux-wheels
```

Summing wheel ZIP members gave 16,910,856 bytes. Native Linux execution, Vercel's
complete build output and real provider latency were not tested. Transitive
dependencies are resolved from the pinned direct runtime requirements; the
repository does not yet include a transitive lockfile.

Ignored local reports: `.pytest_cache/phase3-baseline.xml`,
`phase3-final-review.xml`, matching text output, backend install logs and Linux
wheel logs. Isolated environments, wheel downloads and baseline copies are local
verification artefacts and must not be committed.

## Remaining review gates

- Resolve or explicitly accept the 12 existing test failures before launch.
- Confirm the selected Vercel plan/build uses Python 3.12, the explicit API
  entrypoint, backend-only dependencies and the configured Fluid duration.
- Measure the final function bundle, provider payloads, cold starts and worst-case
  latency. Dependency-wheel size alone is not a Vercel compatibility certificate.
- Verify actual shared Redis admission across hosted instances and service outages.
- Apply hosting controls to invalid-authentication floods and provider spending
  caps; the application quota identifies the frontend server, not individual users.
- Keep the frontend timeout above the backend deadline. Already-sent synchronous
  provider work may finish after an HTTP timeout and cannot be forcibly recalled.

See [assessment and proposed Protected Preview instructions](backend-production-readiness.md).

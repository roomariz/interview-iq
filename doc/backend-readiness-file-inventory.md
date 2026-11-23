# Backend readiness file inventory

Existing staged HTTP backend separation changes were retained. These paths describe Backend readiness only.

## Created

- `api/configuration.py`: local/test/production validation at request admission.
- `api/rate_limit.py`: atomic Redis REST quota and local development option.
- `interview_app_backend/llm/deadline.py`: shared deadline, bounded transport waits.
- `interview_app_backend/llm/fallback_dispatch.py`: existing provider dispatch split
  from its compatibility module to satisfy the 250-line limit.
- `interview_app_backend/llm/fallback_validation.py`: unchanged JSON/network helpers.
- `requirements-backend.txt`: minimal backend runtime pins.
- `requirements-frontend.txt`: independent Streamlit HTTP frontend runtime pins.
- `pyproject.toml`: backend dependency discovery, Python and explicit ASGI entrypoint.
- `vercel.json`, `.vercelignore`: function duration and package/secret exclusions.
- `tests/test_backend_deadlines.py`, `tests/test_shared_rate_limits.py`.
- `doc/backend-production-readiness.md`, `doc/backend-readiness-file-inventory.md`, `doc/backend-readiness-test-results.md`.

## Modified

- `api/security.py`: aggregate HTTP deadline, shared quota admission, concurrency.
- `api/errors.py`: final budget check before returning a service result.
- `config/settings.py`: no repository dotenv loading in test/production mode.
- `interview_app_backend/llm/client.py`: remaining provider timeout, bounded wall
  wait, deadline-aware retries, disabled hidden SDK retries and safer failure logs.
- `interview_app_backend/llm/ollama_client.py`: same request budget, bounded wall
  wait and cancellation-aware backoff; preserve timeout error causes.
- `interview_app_backend/llm/provider_clients.py`: disable hidden SDK retries.
- `interview_app_backend/llm/provider_fallback.py`: preserve deadline exceptions
  across provider retries and compatibility exports for extracted helpers.
- `interview_app_backend/services/question_retry.py`: check budget before corrections.
- `.env.example`, `AGENTS.md`: configuration examples and user scope record.
- `doc/manual.md`, `doc/developer-manual.md`, `doc/test-manual.md`: current behaviour
  and links to production configuration and verification.

No existing test assertions, scores, prompts, frontend screens or provider rankings
were changed. `.pytest_cache/` contains ignored baseline copies, isolated installed
packages, Linux wheels and reports; these are verification artefacts, not commit
contents. No commit, push, remote resource creation or deployment was performed.

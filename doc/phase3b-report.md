# Phase 3B checkpoint — real Redis verification passed

Date: 16 November 2026. This is preparation and local verification, not a completed
cloud deployment. Real Redis verification has now passed; the Preview project
configuration and reviewed source revision remain the next approval/access gates.

## Deployment state

| Deliverable | Observed result |
| --- | --- |
| Vercel Preview URL | Not created |
| Streamlit test URL | Not created |
| Vercel account | Connected; team astraut-solutions-projects |
| InterviewIQ Vercel project | None found; no project created |
| Source | roomariz/interview-iq; public by explicit user choice |
| Source publication | Reviewed preparation commit local on codex/phase3b-preview; push awaits approval |
| Managed Redis | User-created free Upstash database; credentials loaded only into verifier environments |
| Real Redis/two-process verification | Passed: four 200 responses and four 429 responses across two independent processes |
| Vercel build, routing and full bundle | Not executed; no cloud result claimed |
| Streamlit hosted integration/workflow | Not executed |
| Live Ollama / costs / latency | No calls; measurements and cost unknown |
| Production recommendation | Do not release; cloud gates remain unmet |

## Changes prepared

- `deployment/streamlit/app.py` and `requirements.txt`: dedicated Community Cloud
  entrypoint and frontend-only dependency discovery.
- `deployment/streamlit/secrets.example.toml` and
  `deployment/vercel-preview.env.example`: placeholders using actual code settings.
- `interview_app_frontend/services/api_client.py`: optional server-side Vercel
  automation bypass header, needed to reach protected Preview deployments.
- `scripts/verify_managed_redis.py`: opt-in two-process real-service quota, parallel
  admission, authentication, Retry-After and simulated outage verification.
- `interview_app_backend/llm/deadline.py`: fixed an early-timer-wakeup edge case;
  backoff truncated to the remaining budget now always raises deadline expiry.
  The existing deadline test exposed this during the first regression run.
- `.vercelignore`, `vercel.json`: exclude deployment preparation/frontend files
  from the API bundle; `.gitignore`: ignore generated `.vercel/` state.
- `tests/test_phase3b_deployment.py`: five new regression checks.
- `AGENTS.md` and the user/developer/test manuals: public-source clarification,
  Redis gate and current setup links. Existing Phase 3A edits are retained.
- This report, [the proposal](phase3b-proposal.md) and
  [free Upstash instructions](phase3b-upstash-setup.md).

## Verification results

| Check | Result |
| --- | --- |
| Last recorded full suite (before documentation-only update) | 587 passed, 12 failed, 11 deselected; 36.94 seconds |
| Phase 3B tests | All 5 passed |
| Failing identities versus Phase 3A JUnit | Identical; no new failures |
| Changed/new Python lint | Passed |
| Git diff whitespace check | Passed; existing LF/CRLF conversion notice only |
| Frontend-only dependency installation | Passed in clean isolated Python 3.12 env |
| Isolated frontend pip check | No broken requirements |
| Isolated cloud entrypoint rendering | Existing welcome screen rendered |
| Backend-only SDK absence from frontend | OpenAI and FastAPI confirmed absent |
| Existing full mocked HTTP/interview workflows | Included in full suite |
| REST compatibility | Existing httpx/EVAL protocol matches official Upstash docs |
| Real Redis verification | Passed connectivity, parallel quota, Retry-After, invalid auth and fail-closed checks |

The new tests cover the optional bypass header, disabled redirects, secrets kept
out of JSON payloads, frontend entrypoint/dependencies and deterministic early-wake
backoff handling. No existing tests were changed to hide failures.

Reproduce the final suite with APP_ENV=test, LLM_PROVIDER=open-router and dummy
provider keys, then `.venv/Scripts/python.exe -m pytest -q --tb=short`.
Reports are ignored local files `.pytest_cache/phase3b-final.xml` and `.txt`.
Fresh frontend installation uses `deployment/streamlit/requirements.txt`;
`.pytest_cache/frontend-smoke.txt` records its clean-environment render result.
Windows asyncio tests need loopback permission; external provider sockets remain
blocked by the existing suite fixture.

## Known failures: preliminary release impact

These are the same 12 identities documented in [Phase 2](phase2-test-results.md)
and [Phase 3A](phase3a-test-results.md). They were re-observed, not resolved.

| Existing failures | Observed mismatch / release concern |
| --- | --- |
| 2 logger tests | Expect module-named logger, while code uses shared llm logger; review observability expectations |
| 2 mocked OpenRouter tests | Expected SDK args/base URL differ from current configuration; live transport remains unverified |
| 1 transient-model fallback test | Constructs SDK error without required response/body; fallback coverage has a fixture gap |
| 1 scoring-prompt separation test | Expected prompt-separation assertion fails; requires evaluation-contract investigation |
| 3 feedback follow-up tests | Specific wording/progression assertions fail; coaching and memory behaviour require product review |
| 1 supported-techniques test | Expected caching coaching is absent; feedback reliability concern |
| 1 Ollama evaluator test | Four observed calls versus three expected; call budget and actual costs need review |
| 1 trimmed-answer/session test | Missing future_session_memory state; session storage/isolation path needs investigation |

Test age or mocked status is not proof a failure is harmless. The evaluation,
coaching, memory and model-call mismatches remain release gates until investigated
or explicitly assessed and accepted. Scoring and provider rankings were untouched.

## Security findings and limits

No tracked private `.env` or `secrets.toml` files were found. A scoped scan found
no known OpenRouter, Google, GitHub token or private-key patterns in tracked text
or the five locally reachable Git commits. This is not exhaustive secret scanning
and does not certify unreachable/remote history or all credential formats.
No real credentials were printed, included in templates, committed or deployed.

Backend auth and Redis remain separate from Vercel Preview protection. Streamlit
receives no provider or Redis credentials. Shared rate limits identify the frontend
server secret, not individual users. Hosting ingress controls and provider spending
limits remain necessary before launch. Local session-isolation checks pass where
covered, but the retained memory-state failure and hosted multi-user testing remain.
No privacy claim about production logs is possible without an actual deployment.

## Publication preparation update

The reviewed branch is `codex/phase3b-preview`, based on published `83c43f6`.
Frankfurt `fra1` is configured to match the user-confirmed Upstash eu-central-1
region. Automatic Git deployments are disabled in the prepared Vercel config.
A fresh pre-commit suite retained 587 passes and the same 12 failures. The required
dependency audit reported advisories in five packages and is not green; see
[the publication plan](phase3b-publication-plan.md). This is a deployment gate.
No push or cloud configuration change has been authorised by the Git preparation.

## Next action

Real Redis verification passed; see [the sanitised results](phase3b-redis-verification.md).
The [Preview proposal](phase3b-proposal.md) has been reviewed. The connected Vercel
team still has no InterviewIQ project, and the GitHub connector reports read-only
repository access. The reviewed local preparation commit is not yet published to GitHub.
Approve the exact Preview project configuration before its external setup, as
required by Step 5 of the Phase 3B request. Use authorised Git access to publish
the reviewed source before creating its Preview deployment.

There is no basis yet for reporting hosted latency, execution duration, inference
costs or a production-ready hosted workflow. Only expiring Redis verification
counters were written remotely. No Production deployment, live LLM call, paid
infrastructure, source push or Vercel project/environment mutation occurred.

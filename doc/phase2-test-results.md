# Phase 2 verification — 16 November 2026

## Results

| Check | Result |
| --- | --- |
| Unchanged current-commit baseline | 503 passed, 13 failed, 11 deselected |
| Final full suite | 554 passed, 12 failed, 11 deselected |
| New Phase 2 tests | 50 passed |
| New failing test identities relative to baseline | None |
| Changed Python files: Ruff | Passed |
| Whole repository: Ruff | 46 existing findings; see limitation below |
| Deployment / live provider requests | None |

Pre-commit `pip-audit` of the unchanged direct pins found 12 known vulnerabilities:
Streamlit 1.40.0 (4), python-dotenv 1.0.1 (2), requests 2.32.3 (4), and fpdf2 2.7.8
(2). The audit used `--no-deps --disable-pip`, so transitive dependencies were not
audited. Dependency upgrades remain separate work; no automatic fixes were applied.

The pasted Phase 1 total of 343 passing tests predates the current repository.
The unchanged current commit has 516 selected tests. Its baseline was extracted
under ignored `.pytest_cache/phase2-baseline`; no tracked source was reverted.
JUnit identities, rather than totals, were compared. All 12 current failures
also fail in that baseline. The existing sample-answer storage test now passes
with the frontend's provider-independent configuration and mocked rewrite.

Final suite time was about 33 seconds. XML/output reports are in ignored
`.pytest_cache/phase2-current.xml`, `phase2-baseline.xml` and neighbouring output
files; these are local artefacts, not application data or files to commit.

## Reproduce

Use `.venv/Scripts/python.exe`; the system interpreter has incompatible FastAPI
and OpenAI versions. The project virtual environment matches the pinned
FastAPI 0.115.6, httpx 0.27.2, OpenAI 1.109.1 and Pydantic 2.10.0 versions.
For the comparable full-suite run, select OpenRouter with dummy test keys:

```powershell
$env:LLM_PROVIDER = 'open-router'
$env:OPENROUTER_API_KEY = 'local-test-key'
$env:GOOGLE_API_KEY = 'local-test-key'
$env:XAI_API_KEY = 'local-test-key'
.venv/Scripts/python.exe -m pytest -q --tb=short
```

Run the five `tests/test_phase2_*.py` modules listed in the test manual for focused
verification. The external-network fixture blocks non-loopback sockets throughout
the test process. Windows asyncio needs loopback socket pairs: sandboxed attempts
hung before API tests started, so completed runs used local loopback permission.
No live Ollama smoke test was authorised or performed.

The unchanged baseline uses dummy provider credentials, never a copy of private
keys. An attempt to pass the full private environment to that subprocess was
rejected by automatic approval review and was not executed.

## Coverage of the migration

- Authentication and missing server configuration; public health and OpenAPI.
- Request schemas, exact question counts, answer limits, prompt markers,
  oversized/chunked requests, malformed JSON, concurrency and local rate limits.
- Actual question service and evaluation pipeline with mocked SDK JSON responses;
  score/trust preservation and provider failures without placeholder scores.
- Frontend timeout, connection, HTTP status, invalid response, count mismatch,
  redirect prevention, environment and Streamlit-secrets handling.
- Complete setup → question → evaluation → follow-up → next question → summary
  through the HTTP client, plus isolated snapshots/defaults and stale-work reset.
- Real Streamlit rendering, answer submission and summary against a local Uvicorn
  server using synthetic inputs and mocked services, with no provider network.
- Static import check: frontend code does not import provider SDK modules,
  backend business services, `config.settings` or `config.model_profiles`.

Streamlit 1.40 AppTest cannot serialise this screen's segmented controls correctly.
The local-render test supplies setup values to the normal setup callback, then
interacts with rendered answer/feedback screens. Browser setup widgets and two
independent browser sessions remain manual checks in `doc/test-manual.md`.

Existing UI tests were explicitly adapted: `tests/question_loop_support.py` polls
the frontend HTTP job; fixtures in `tests/conftest.py` and
`tests/phase2_legacy_support.py` bridge existing service doubles to mocked HTTP.
They finish workers inside each patch scope. Existing assertions were not edited.

## Existing failures retained

These exact identities fail in both baseline and final runs:

```text
tests/test_api_error_handling.py::TestApiErrorHandling::test_call_llm_logs_empty_output
tests/test_client_configuration.py::TestClientConfiguration::test_call_llm_logs_task_and_model
tests/test_example_answer_prompt.py::TestExampleAnswerPrompt::test_evaluate_answer_keeps_scoring_prompt_separate
tests/test_feedback_screen.py::TestFeedbackFormatting::test_follow_up_for_irrelevant_answers_is_direct
tests/test_feedback_screen.py::TestFeedbackFormatting::test_follow_up_stage_advances_with_memory
tests/test_feedback_screen.py::TestFeedbackFormatting::test_follow_up_uses_issue_context
tests/test_mocked_openrouter_call.py::TestMockedOpenRouterCall::test_call_llm_uses_mocked_openrouter_response
tests/test_mocked_openrouter_call.py::TestMockedOpenRouterCall::test_get_openrouter_client_returns_configured_client
tests/test_model_availability.py::TestModelFallbackLogic::test_transient_free_model_retries_then_moves_on
tests/test_negative_hallucination.py::TestNegativeHallucination::test_feedback_can_mention_techniques_actually_in_answer
tests/test_ollama_workflows.py::test_existing_evaluator_validates_evidence_and_scores
tests/test_session_manager_trimmed_answer.py::test_submit_answer_persists_trimmed_answer
```

These failures concern existing logger/mock expectations, follow-up expectations,
provider assumptions and feedback-storage behaviour; they were not rewritten to
make the migration green. Whole-repository lint also remains non-zero. Changed
Python files pass; unrelated lint clean-up is outside Phase 2.

## Limits of this verification

This confirms local mocked behaviour, not real-provider latency, production
capacity, Linux bundle size or deployed routing. The actual provider calls may
outlast the frontend timeout; distributed quotas and package trimming remain
Phase 3 prerequisites described in [the integration review](phase2-integration.md).

# Question-two failure investigation and correction

18 November 2026. Phase 6A; local correction only, on
`feat/streamlit-vercel-backend`. No push, deployment or live inference.

## Confirmed cause

The retained Preview's **static mock provider fixture** returns the same five
questions for every request. At question two, the request correctly includes
question one's text in `previous_questions`. The real validator rejects the
repeated first question, all three mock retries repeat it, and the deterministic
fallback also fails the existing previous-question check. The resulting
`RuntimeError("Fallback generation failed validation: question[1]: duplicate_previous_question")`
is caught by `SafeRoute` and returned as sanitised HTTP 502 `provider_failure`.

This is not evidence that the frontend should cache its first response. Existing
behaviour requests a fresh candidate batch for each adaptive step, displays its
first question and retains the batch for that step. Changing this into a fixed
initial questionnaire would change adaptation. The earlier caching suggestion
was a hypothesis and is superseded by this investigation.

## Evidence before modification

- Read-only Vercel inventory: **104/104 uploaded source SHA-1 hashes** matched the
  retained local artefact. Its SHA-256 inventory also matched the historical
  manifest. The deployed artefact was not edited.
- Exact-source local replay, with external sockets blocked: first question 200;
  second question 502; terminal exception above. Four synthetic question outputs
  total: one initial success, three rejected second-step attempts. Zero real calls.
- Scoped runtime log retrieval returned **67 records** within the available Hobby
  retention window, including nine question-rejection messages and three terminal
  fallback-validation messages. Dynamic reasons were redacted by existing logging;
  no unredacted hosted exception is claimed. The exact internal reason comes from
  deterministic replay of the verified source and synthetic request history.
- Connector logs returned 403; the existing personal-scope CLI succeeded after
  using the available 15-minute retention window. The one-hour query was rejected
  by retention, not interpreted as an absence of logs. No auth settings changed.

## Workflow trace and exclusions

1. Setup calls `/context`, resolving the non-free mock profile to five candidate
   questions and five interview steps. Streamlit owns all interview state.
2. `begin_question_generation` snapshots inputs, gap/adaptation state, index and
   previous answers into an authenticated request; credentials are resolved before
   worker dispatch. The HTTP client has no automatic POST retries.
3. API request count/schema validation passes. The service requests and validates
   the full five-item bundle. The frontend selects its first item for the step.
4. Evaluation stores the answer once and updates adaptation. Next increments the
   index, clears only the old step's candidates and requests a fresh batch with
   recent question history. The static mock violated this new request's contract.
5. Duplicate rejection and fallback failure occur inside the service, before
   FastAPI response validation. Schema rejection is 422; wrong count and malformed
   provider output remain rejected rather than silently accepted.
6. Redis quota denial is 429, shared-service outage 503 and deadline expiry 504.
   The replay does not use Redis and still reproduces 502, excluding admission as
   its cause. Hosted logs and the earlier status trace agree with service failure.
   Leases/deadlines wrap the route and are released by existing finally paths.

Authentication, Redis scripts/limits/namespace, leases, aggregate deadline,
provider retry policy, normal API adapters, prompts and scoring were not changed.

## Minimal correction

- `deployment/mock_questions.py`: finite deterministic synthetic question bank,
  keyed by the explicit interview index; emits exact one/five-item contracts,
  source grounding and ordered scenario coverage. ContextVar binding isolates
  concurrent requests and is reset on success/error. Supports five mock steps.
- `deployment/mock_preview.py`: preserves the original permanent mock transport
  guards and evaluation outputs; replaces only its static question reply with
  the request-aware fixture. Installed only by the isolated artefact entry point.
- Frontend `question_generation_job.py`: do not dispatch another request while a
  future is unconsumed; empty/invalid/error results remain at the same preparing
  step with history and identity intact. No automatic retries.
- Preparing screen: an explicit **Retry question** action retries that step, rather
  than returning to setup and encouraging a session reset. Existing screens remain.
- `scripts/package_mock_preview.py`: local backend-only packaging with an explicit
  source revision, two flattened mock overlays and a hashed source inventory.
  No upload/deploy capability. Normal backend startup never installs these mocks.

No initial-batch caching, new live-provider request, scoring change or provider
substitution was introduced. Mock replies still pass the normal schema, grounding,
scenario, count and duplicate checks. The published old Preview still has its
original fixture; this correction is not yet hosted.

## Regression tests

| File | Coverage |
| --- | --- |
| `tests/test_mock_question_progression.py` | Original fixed-fixture failure and exact terminal cause; five fresh steps in one/five-item modes; role-only and two CV/JD cases; exhaustion/context cleanup |
| `tests/mock_question_support.py` | Shared provider double that retains the real generation/parser/validation pipeline and counts attempts |
| `tests/test_local_streamlit_backend.py` | Real loopback HTTP; three/five answers; question order, full candidate batches, summaries, reruns, per-step evaluation count and explicit second-step recovery |
| `tests/test_question_progression_recovery.py` | Empty/invalid batches, backend errors, identity/history/index preservation and unconsumed-future dispatch protection |
| `tests/test_mock_preview_artifact.py` | Exact packaged backend, startup refusal for Production/live keys/fallback and isolated subprocess execution |
| `tests/mock_preview_artifact_check.py` | Five real pipeline evaluations/follow-ups plus example answer; five question attempts; all four provider origins blocked through Requests and sync/async HTTPX |

The local HTTP tests compare question order with stored evaluations and assert
one synthetic provider output per successful step. An injected second-step HTTP
failure occurs before provider generation; reruns do not retry. Explicit retry
continues the same index, without another evaluation of question one or identity
reset. Free mode ends after three answers; five-item mode ends after five answers.
Exhaustion never silently wraps to question one or starts another request.

## Verification

Final complete working-tree suite: **750 passed**, 11 live/browser tests excluded,
no skips, five existing warnings, 63.70 seconds. This includes disposable real
Redis and the new isolation/CV regressions. The exact isolated correction tree also
passed its complete suite: **735 passed**, 11 live/browser tests excluded, no skips,
five warnings, 61.17 seconds. Its 15-test difference is the earlier uncommitted
Community Cloud demonstration tests, deliberately excluded from this commit.

Repeated advisory audits: frontend **40**, backend/development **82**, installed
environment **96** packages; zero known vulnerabilities. `pip check` passed.
Changed-file Ruff passed. Whole-repository baseline lint findings are unrelated.
Configured-value/credential-pattern scans cover candidate source, staged changes,
reachable history, proposed artefact and private diagnostic output; values are
never included in reports. Advisory/scanner limits remain point-in-time/bounded.

Full tests use disposable local Redis, not managed counters. External networking
is blocked in the suite and in packaged-runtime checks. Shared quota, identity,
lease ownership/renewal/release/expiry and deadline regressions remain enabled.
No old Preview request was retried during this investigation; hosted work was
read-only metadata, source hashes and retained logs.

## Commit and remaining gates

The correction is committed separately from earlier staged descriptive renames
and Community Cloud demonstration preparation. Only the touched HTTP test's
descriptive rename is included; the other staged renames remain staged.
Earlier demonstration assertions in that test remain a separate local change.
The three manuals and AGENTS log receive only this correction's added references
in the correction commit; their earlier staged/unstaged edits are preserved.
Generated/private artefacts remain ignored, never committed.

The retained mocked Preview and inert Production bootstrap are unchanged.
Replacement hosted verification, its source upload, any branch push and Community
Cloud deployment each remain unapproved. Full hosted compatibility is therefore
still a deployment blocker. A finite synthetic fixture cannot establish live AI
quality or unrestricted model behaviour.
See the [exact protected replacement proposal](mock-question-preview-proposal.md).

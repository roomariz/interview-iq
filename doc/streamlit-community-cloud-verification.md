# Community Cloud preparation verification and operations

18 November 2026, Europe/Berlin. **Preparation only; nothing deployed or pushed.**
The previous historical mock-blocker report is superseded by the
[successful hosted backend run](hosted-workflow-recovery-results.md).
The backend is `dpl_3XLLkftWMZQx7U8bJwjXJG6NraRt`; its runtime bytes remain frozen.
See [exact deployment configuration and approval boundary](streamlit-community-cloud-proposal.md).

## Local corrections and readiness

- Keep `deployment/streamlit/app.py` as the entrypoint and its adjacent requirements
  include as dependency selector; keep Python 3.12 and existing frontend pins.
- Lock the cloud configuration and template to the verified immutable Preview URL.
  Reject old deployments, other origins, query strings and missing/placeholder keys.
- Existing demonstration-mode changes are included in the scoped release candidate:
  persistent notice, feedback download provenance, safe configuration gate and theme.
- No evaluation scoring, provider choice, backend admission or Redis configuration change.
- Real backend/bypass/signing credentials are prepared only in an ignored private
  TOML handover. None is copied into public source, generated manifest or this report.
- Root private `.streamlit/secrets.toml` is never created, overwritten or published
  by this preparation. Only `.streamlit/config.toml` is eligible for publication.
- Unrelated staged renames and working-tree edits are excluded from the candidate.

## Evidence levels

Local tests exercise real Streamlit secrets resolution and the frontend HTTP client,
with synthetic keys and mocked backend responses. They verify all three headers,
signed visitor validation, no automatic POST retry, redirect refusal and safe error
messages. The browser-facing protocol elements and downloadable report contain no
configured secret values. The Python AppTest container intentionally holds its own
private test secrets; its object representation is not treated as browser traffic.

The prior hosted backend run demonstrated the same server-to-server path with real
private credentials, five questions/evaluations, state preservation, quota denial,
owned lease renewal and recovery by the expiry observation. No new hosted API or
managed Redis probe was needed during this preparation. Actual Community Cloud
network reachability, private account eligibility, build selection, browser capture
and deployed rollback remain unverified until separately approved execution.

## Local verification receipt

Final automated results, exact candidate tree and file hashes are recorded below
when preparation completes. Private raw test/audit/scan receipts remain ignored in
`.verification-local/community-cloud-preparation/`. The source candidate is based
on `e247aba`; it is not a new published release commit. Do not deploy that existing
SHA expecting the uncommitted cloud guard/demo changes to be present.

Checks cover cloud configuration failure before any API call, actual `st.secrets`
header forwarding, signature validity, download demonstration provenance, full
five-question UI progression/recovery, API contracts and existing quota controls.

## Timeout and temporary concurrency procedure

| Signal | Action |
| --- | --- |
| Safe question-generation 502 | Preserve history/index/identity; one explicit Retry question only if within approved test budget |
| 429 quota/busy | Keep the same session; respect Retry-After on the server side or wait for the minute window; do not clear counters or rotate identity |
| 503 Redis/service unavailable | Fail closed; retain inputs, stop repeated clicks and wait; check redacted server logs, not raw upstream error text |
| 504 or transport timeout | Keep state; do not assume that the server did no work or that the lease is already released |
| Uncertain evaluation response | Do not automatically resubmit; pause the controlled test and reconcile safe dispatch/status evidence before a further approval |
| Persistent concurrency exhaustion | Check operator evidence within the correct namespace; a lease can remain up to 330 seconds from its last renewal; no manual deletion |
| Authentication redirect/401 | Stop; verify the private secret source and exact backend origin; never disable Vercel protection to continue |

The existing client shows a friendly wait/unavailable message; it does not display
raw credentials or automatically retry POSTs. The manual operator can inspect
Retry-After privately. Question errors retain their step and have an explicit retry
action. A lost evaluation response is not guaranteed idempotent: the API is stateless,
so do not describe manual resubmission as exactly-once execution.

Never lower quotas, reset Redis, call a different provider, increase timeouts or
redeploy the backend merely to bypass a wait. The frontend timeout is 180 seconds;
backend aggregate deadline remains 150 seconds. The earlier 121-second synthetic
504 reflected the provider transport retry budget inside that aggregate deadline.
Natural expiry recovery passed; immediate post-timeout cleanup was not proved.

## Monitoring during the approved smoke test

- Restrict to the owner and synthetic inputs. Record the exact app/release/backend
  identifiers, first request time and one anonymous session, without public token.
- Count backend requests at dispatch and response, including failed/denied attempts;
  record path, status, duration and question index only. Do not print request headers,
  bearer/bypass values, visitor tokens, CV/JD contents or complete answer text.
- Reconcile five generation successes, five evaluations, final answer count and
  summary averages; rerenders must not add generation/evaluation requests.
- Streamlit build logs must select the adjacent frontend manifest and Python 3.12.
  Browser Network must not show direct backend requests, auth headers or secret
  values in JavaScript, WebSocket UI messages or downloads. Redact evidence locally.
- Inspect Streamlit and Vercel logs privately; retain safe status/count/timing data.
  Do not expose an operator diagnostic panel or copy raw environment/log output.
- Preserve the established namespace/limits. Do not rerun concurrency saturation,
  long timeout probes or daily exhaustion for frontend release approval.
- Stop at the approved caps, an unknown evaluation outcome, broken privacy,
  credential exposure, critical regression, live-provider traffic or required spend.

## Rollback instructions

Before creation, leave the source local and undeployed. A first app has no known-good
predecessor: stop it and, only with scoped approval, delete that new Streamlit app
and its private secret copy. Keep local redacted evidence and the reviewed source.
Do not delete another private app to obtain a free private slot.

For a later frontend update, restore its recorded previous frontend commit on the
approved release branch and rebuild. Do not merge to main or change backend aliases,
variables, authentication, Redis keys, deployments or the inert Production bootstrap.
A code push to an already connected app can rebuild it, so no publication is part
of this preparation. A Python-version change requires a separate recreation plan.

If a credential may have leaked, stop the test and remove only the new frontend's
private copy if approved. Request coordinated rotation separately: the existing
backend bearer, visitor signing key and project bypass are shared capabilities.
Do not unilaterally revoke them or modify the protected backend to restore access.

## Approval checklist and unresolved gates

Review the exact candidate inventory, source patch, private template and proposed
12-admission/16-backend-HTTP smoke-test cap in the linked proposal. Approve scoped
feature-branch publication, one initially inactive public shell followed by verified
owner-only sharing, private secret installation and the bounded test separately.
No email invitations, public active release, paid resources or live inference.

Stop if the requested subdomain is unavailable, the owner/workspace differs, the
single free private slot is unavailable, or account access cannot be established.
No account, deployment, sharing or credential setting has been changed here.

## Final preparation results

| Check | Result |
| --- | --- |
| Complete working-tree suite with disposable Redis | 769 passed; 11 live/e2e deselected; five existing warnings; 87.43 seconds |
| Exact scoped release candidate suite | 769 passed; 11 live/e2e deselected; five existing warnings; 87.59 seconds |
| Focused configuration/header/download/local UI checks | 28 passed before adding three further waiting/question notice cases; those cases passed in the complete suite |
| Frontend-only entrypoint | Welcome and persistent demo notice passed; FastAPI/OpenAI/Google SDKs absent |
| Actual local frontend-only server | Health and root returned 200; loopback only; synthetic settings; no backend work |
| Frontend requirements audit | 40 resolved packages; zero known advisories |
| Development audit | 82 resolved packages; zero known advisories |
| Installed environment audit | 96 packages; zero known advisories |
| pip check | Main and isolated frontend environments passed |
| Changed Python lint | Passed |
| Secret scans and candidate hash | See ignored `community-cloud-preparation/candidate.json` and scan receipt; no secret values printed |

Both final suites set `LEASE_EXPIRY_TEST_MS=2000` only for the isolated local crash
regression. Earlier runs using its default 500-ms lease had one timing failure:
client startup outlasted the lease before the busy assertion. No production code
or 330-second lifetime was changed. The earlier full 330-second termination test
and hosted lease recovery remain the backend evidence, not a shortened equivalent.
Streamlit 1.67 requires Uvicorn transitively; its presence is normal in the isolated
frontend environment and does not install the application's FastAPI/provider SDKs.

The exact candidate has 17 scoped paths, based on `e247aba`. Its private review
patch and inventory live in `.verification-local/community-cloud-preparation/`:
`.gitignore`, root theme, the cloud entrypoint/template, frontend app/feedback/gate,
cloud and workflow tests, the existing tracked Preview test, manuals, constraint
history and the three directly relevant preparation/backend-result documents.
The existing Preview test retains its committed filename; unrelated rename work
is excluded. The candidate tree/hash is held separately to avoid a self-referential
manifest inside the tree. No new release commit, push or deployment was made.

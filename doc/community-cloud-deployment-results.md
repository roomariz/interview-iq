# Private Community Cloud deployment results

Reported 19 November 2026 (Europe/Berlin). **Private app created; startup blocked.**

- URL: <https://interviewiq-demo.streamlit.app/>
- Workspace: `roomariz`; no viewer invitations were added.
- Repository: `roomariz/interview-iq`.
- Branch: `feat/streamlit-vercel-backend`.
- Commit: `a3917a734577814d5aa06a67725181265f771c30`.
- Exact reviewed 17-file tree: `b2bc75de7329e8f963120b8b2d0fd1408a8901fc`.
- Entrypoint: `deployment/streamlit/app.py`; Python 3.12.16.
- Intended backend: protected mock `dpl_3XLLkftWMZQx7U8bJwjXJG6NraRt`.

## Source and local checks

Only the approved candidate was committed and pushed. Unrelated staged renames
and working-tree changes were excluded and retained locally. Main remained
`164fe226c95af6259d5f67170e1e20965d4c280b` after publication.

The committed tree and all 17 file hashes matched the preparation inventory.
The private handover's credential values were absent from the candidate archive.
Changed Python lint passed. A refreshed installed dependency audit found no known
vulnerabilities. Focused candidate tests passed: **30 passed**, two deprecation
warnings, 32.80 seconds. The initial sandboxed focused run stalled during UI
initialisation and was terminated; the successful run used the same exact isolated
candidate outside the sandbox with its external-network test guard enabled.
Earlier complete candidate verification remains 769 passed, 11 deselected.

## Creation and access controls

The app was created without any backend secrets. Python 3.12 was selected explicitly;
build logs confirmed dependencies were selected from
`deployment/streamlit/requirements.txt`, rather than the root backend manifest.
Community Cloud replaced transitive PyArrow 26.0.1 with 24.0.0 and added its normal
logging packages. The deployed environment therefore includes platform adjustments.

The initial public shell failed before configuration or interview actions:
`ModuleNotFoundError: No module named 'interview_app_frontend'` at entrypoint line 3.
No backend client was constructed and no authenticated backend request could run.
The intended configuration-error screen was not reached because imports failed first.

Sharing was changed to **Only specific people can view this app** and saved.
A separate signed-out in-app browser was redirected to Community Cloud and displayed
**You do not have access to this app or it does not exist**, with sign-in controls.
This confirmed denial before any credential installation. The private setting was
accepted without an allowance or paid-plan error. No existing app was changed.
Repository push-access holders retain management access; their roster has not yet
been independently verified, so owner-only credential eligibility remains incomplete.

No credentials were installed. Browser-traffic/log checks involving real secrets
were therefore not exercised; credential containment with installed secrets is
unverified. No live inference, paid infrastructure or new expenditure was initiated.

## Workflow results and request ledger

| Check | Actual result |
| --- | --- |
| Backend HTTP attempts | **0 / 16** |
| Admitted backend requests | **0 / 12** |
| Context, question generation, evaluations | None dispatched |
| Five-question hosted workflow | Blocked by startup import failure |
| Hosted adaptive progression, summaries and downloads | Not exercised |
| Backend response times | Not applicable; no requests |
| Failure | Frontend startup import error; no backend/provider failure |

Browser navigation, build downloads and read-only GitHub/Vercel control-plane
inspection are separate from backend verification HTTP attempts. No Redis diagnostic
request, identity rotation, counter reset, concurrency probe or provider call occurred.

## Remaining work and boundary

Read-only before/after comparison confirmed the same five Vercel deployment records,
including the inert Production bootstrap, and unchanged metadata fields. All 20
shared environment records were unchanged. All Deployments protection, project
resources, Hobby plan and disabled Git deployment controls were preserved. No Vercel
deployment was created and no backend quotas or lease configuration was modified.

The nested entrypoint cannot resolve the repository package in the hosted runtime.
Local AppTest verification did not reproduce that runtime import-path condition.
A corrected, reviewed source commit and hosted rebuild are required before secrets
or the bounded workflow can proceed. The exact approved candidate was left deployed;
no unreviewed corrective commit was pushed. Public release remains unauthorised.

Private receipts and access-denial screenshot are in the ignored directory
`.verification-local/community-cloud-preparation/`. Credentials are absent from this
report. The Vercel before/after comparison is recorded alongside those receipts.

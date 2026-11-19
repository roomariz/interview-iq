# Streamlit nested-entrypoint startup correction

19 November 2026 (Europe/Berlin). Local correction only; no push or hosted rebuild.

## Cause and evidence

The existing private application's logs show Python 3.12.16 installing dependencies
from `deployment/streamlit/requirements.txt` and executing
`/mount/src/interview-iq/deployment/streamlit/app.py`. Its first project import fails
with `ModuleNotFoundError: No module named 'interview_app_frontend'`.
The cloned repository exists, but its modules were not installed as a distribution.
The frontend manifest includes only third-party frontend dependencies. The root
`pyproject.toml` describes the backend and its provider dependencies; Community Cloud
selected the adjacent requirements file instead. Installing that backend project
would broaden the frontend's dependencies and is unnecessary for this correction.

The frontend and shared directories use Python namespace packages, with no
`__init__.py` files. Python 3.12 supports these packages when their parent is on
`sys.path`; adding initialisation files alone cannot make a missing parent visible.
Streamlit 1.67's installed `modified_sys_path` implementation adds the script's
directory, here `deployment/streamlit`, rather than the repository root. A console
launcher need not include the working directory in the import path. Earlier pytest
and `python -m` checks supplied that root implicitly. Health/root HTTP responses
alone also did not execute a browser session's script.

An isolated Python subprocess reproduced the same import error even with its working
directory set to the repository root. This distinguishes the import path from the
working directory. Exact hosted `cwd` and `sys.path` values are not in the existing
logs and were not instrumented: doing so would require an unapproved hosted rebuild.
The root/entrypoint/unrelated-directory regressions verify independence from `cwd`.

## Smallest correction

Before project imports, the nested entrypoint resolves
`Path(__file__).resolve().parents[2]` and adds that directory to `sys.path` if absent.
This uses the entrypoint's own location, never a machine-specific path or `cwd`.
Repeated script execution does not insert duplicate root entries. No packaging,
dependency pins, provider settings, API contracts, interview logic, credentials,
authentication, quotas or concurrency controls are changed.

The existing guard remains before `main(demonstration=True)`: without backend
configuration it displays the approved-backend configuration notice and stops.
This is the intended inactive state; startup requires no backend credentials.

## Verification

The regression initially failed with the same missing-package error. Results:

| Check | Result |
| --- | --- |
| Exact isolated candidate suite | 742 passed; 30 skipped; 11 live/e2e deselected; five existing warnings; 64.50 seconds |
| Isolated import regression | Passed from repository root, entrypoint directory and unrelated temporary directory using Python `-I` |
| Clean frontend-only environment | Python 3.12.7; 41 installed packages; backend/provider SDKs and backend distribution absent |
| Clean-environment imports | All three working-directory cases reached the inactive notice without credentials |
| Real console-equivalent Streamlit server | Loopback health/root 200; actual WebSocket session executed the same entrypoint and returned the inactive notice, no exception or interview button |
| Dependency consistency | All 41 frontend packages compatible |
| Frontend and development dependency audits | No known vulnerabilities in either environment |
| Changed-file lint | Passed |
| Secret scans | Candidate archive/diff and reachable Git history passed configured-value and credential-pattern checks |

All tests use synthetic settings and block external provider/backend requests.
Existing mocked interview workflow tests, including five-question progression and
retry recovery, passed. The 30 skips are opt-in Redis/service tests without their
required local service configuration; no Redis or backend runtime code changed.
The first broad run had a three-second AppTest timeout in the unchanged
generating-question notice test; that file passed unchanged on rerun. The first
isolated full suite also had six packaging setup errors because Git was resolving
paths relative to the nested review directory. Setting explicit `GIT_DIR` and
`GIT_WORK_TREE` for that test process resolved them; the final suite passed.
The initial clean-server run passed protocol assertions but Windows delayed
temporary-directory cleanup. The final run stopped its own process tree and passed.

Seven files form the correction: the entrypoint, isolated regression tests, this
report, all three manuals and the scoped constraint log. Only documentation was
finalised after the successful tests; tested Python bytes are checked before commit.
Backend verification accounting remains **0/16 attempts and 0/12 admissions**.
Private logs, audit and scan receipts remain ignored under
`.verification-local/streamlit-startup/`.

## Proposed rebuild after separate approval

1. Review and approve the separately recorded correction commit and its seven-file
   diff against `a3917a7`. Unrelated staged renames and working-tree files are excluded.
2. Confirm the remote feature branch still points to the expected published parent;
   stop if it has diverged. Push only `feat/streamlit-vercel-backend`, without force.
   A push can automatically update the already connected Community Cloud app.
3. Use the existing `interviewiq-demo.streamlit.app` application. Preserve the
   repository, branch, entrypoint, Python 3.12 and restricted-viewer settings.
   Do not create another application, change privacy, or install secrets.
4. Observe the automatic update and logs. If it does not pick up the approved
   revision, use the existing app's reboot control only within that rebuild approval.
   Confirm the source revision and frontend dependency manifest selection.
5. Confirm the inactive configuration notice replaces the import traceback; no
   interview buttons or authenticated backend requests should be available.
   Recheck signed-out access denial without changing sharing settings.
6. Stop with the rebuilt source/status report. Credentials and the hosted mocked
   workflow remain a separate stage; this correction itself consumes no backend
   verification attempts or admissions. Do not change any Vercel deployment.

The hosted application remains on `a3917a7` until that publication is approved.
Hosted Linux execution of the corrected code remains unverified at this stage.

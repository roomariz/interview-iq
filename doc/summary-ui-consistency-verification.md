# Summary UI consistency and controlled update proposal

19 November 2026 (Europe/Berlin). Local corrections only; no commit, push or
deployment performed. Hosted workflow success is the user-supplied baseline,
also recorded in the earlier private workflow receipt. This task did not repeat
hosted interview requests or change any cloud settings.

## Root causes and authoritative definitions

The summary renderer searched `{0: Needs Work, 4: Needs Work, 7: Good,
9: Excellent}` in ascending insertion order. Every non-negative average matched
zero first. It now searches descending: below 7 Needs Work, 7 to below 9 Good,
9 to 10 Excellent. Numerical scores and thresholds are unchanged.

The primary PRD delegates structured scoring to the requirements and evaluator.
`product_requirement/product-requirements.md`, FR-4.2, specifies individual
dimension bands: 0–3 Weak, 4–6 Needs improvement, 7–8 Strong, 9–10 Excellent.
`feedback_model.score_band` implements these bands; the current feedback screen
renders numerical dimension scores, rather than the summary band names.
The evaluator prompt defines evidence-based dimension rubrics; model output is
parsed and validated before display. None of that logic was changed.

`shared/scoring.py::derive_overall_decision` is the deterministic answer verdict:
mean of five integer dimensions at least 7 AND reasoning at least 6 gives pass;
mean below 5 OR reasoning at most 4 gives fail; otherwise borderline pass.
Relevance gating can force failure. Confidence describes assessment reliability.
These rules and their existing evaluation adjustments remain unchanged.

`session_summary_view._build_summary_from_raw` is the active session aggregation:
average each required dimension over valid stored answers, round to one decimal,
then average those dimension averages and round to one decimal. Overall 7 or
above gives Good; below 7 gives Needs Improvement. Percentage is the rounded
overall multiplied by ten. Existing supplied summaries are retained.
The legacy backend `report_service.summarise_performance` uses its older report
dimensions and the same overall 7 threshold; it is not this screen's aggregation.
No calculation, scoring weight, stored score or historical verdict was changed.

An answer with scores 8,8,8,7,4 averages 7 but fails its reasoning gate; a session
with those averages still displays 70% (Good). Tests explicitly preserve this
distinction. Summary dimension bands and session readiness are separate too:
9/10 is Excellent in the breakdown while overall readiness remains Good.
Old mockups contain illustrative fractional examples; this fix preserves the
implemented thresholds rather than redefining them from those examples.

Normalised feedback exposes its takeaway at `summary`. Answer-history storage
incorrectly read `feedback.summary`, leaving every saved takeaway blank.
Storage now reads the existing normalised value. The recap also normalises
compatible current feedback to backfill blank legacy takeaways and lists;
explicitly mismatched question/answer feedback is rejected. Legacy feedback
without identifiers retains its existing current-session fallback behaviour.
Recorded key issues are shown when improvement notes are absent. Earlier answer
records are retained; the view does not rewrite history, recalculate evaluations,
generate feedback or request models. Truly absent takeaways remain absent.
Recap text is HTML-escaped before interpolation into its existing HTML layout.

## Scoped files

| File | Change |
| --- | --- |
| `interview_app_frontend/components/session_summary_screen.py` | Descending bands and escaped recap |
| `interview_app_frontend/state/session_feedback.py` | Store existing normalised summary |
| `interview_app_frontend/utils/session_summary_view.py` | Compatible feedback fallback and existing issues |
| `tests/test_summary_presentation_regression.py` | 25 threshold, recap, history and escaping cases |
| `doc/manual.md` | User behaviour reference |
| `doc/developer-manual.md` | Implementation reference |
| `doc/test-manual.md` | Regression and browser check reference |
| `AGENTS.md` | Scoped constraint log |
| This report | Findings, update proposal and rollback |

Unrelated staged renames, requirement edits and existing local work are excluded
from the proposed nine-file update. All scoped files remain within 250 lines.

## Automated verification

| Check | Result |
| --- | --- |
| New regression tests before fixes | 10 failed, 15 passed; reproduced defects |
| Focused new and existing summary tests after fixes | 48 passed |
| Full working-tree suite with isolated test settings | 767 passed, 30 skipped, 11 deselected; five existing warnings |
| Exact isolated nine-file candidate on remote parent | 767 passed, 30 skipped, 11 deselected; 45.08 seconds |
| Five-question local Streamlit/FastAPI workflow | Passed, including generation retry recovery, one evaluation per question, identity retention, correct averages and demo JSON |
| Runtime manifests audit | 49 packages, zero known advisories |
| Development manifest audit | 82 packages, zero known advisories |
| Installed environment audit | 96 packages, zero known advisories |
| Dependency consistency | `pip check` passed |
| Four changed Python files | Ruff passed |
| Secret scan | 361 non-ignored files, scoped snapshot, staged/unstaged diffs and reachable history; nine known values and seven credential patterns; zero findings |

The suite uses `APP_ENV=test`, `LLM_PROVIDER=open-router`, in-memory rate limiting
and no default visitor signing key; tests override settings for their own cases.
The network guard blocks external connections. Initial sandbox execution stalled;
the first unrestricted run inherited private local deployment settings and had
28 API/deadline failures. The isolated test run passed without product changes.
Initial sandbox audits could not resolve PyPI; read-only network-enabled reruns
passed. The 30 skips require opt-in local Redis/services; 11 live/e2e cases remain
excluded by project policy. No fresh real Redis or hosted quota probe was run.
Mocked authentication, API contracts, adaptive progression, quota/lease controls,
model configurations, session identity and demonstration tests passed.

## Browser credential protection: partial inspection only

The authenticated existing Chrome tab opened the hosted welcome page at
`https://interviewiq-demo.streamlit.app/`. The application iframe displayed the
demonstration notice with zero rendered exception elements. The shell/iframe DOM
and the one available console entry had no tested credential markers. Only
origins/paths, counts and booleans were emitted; no credential values were shown.
This was a marker check, not an exact-value comparison or complete JS/config audit.

The supported browser API exposes DOM, console and assets, but no network-header
or WebSocket-frame capture. HTTP request/response headers, WebSocket handshake and
messages, runtime configuration beyond the DOM, hosted error paths and a fresh
hosted feedback download therefore remain UNVERIFIED in this task. The welcome
screen had no download; this task did not run a new hosted workflow. The earlier
download/log findings are historical evidence, not a new traffic verification.
Local tests confirm synthetic server secrets remain in server request headers,
safe error messages and demonstration-labelled downloads exclude those secrets.
Source review confirms backend credentials are read server-side and are not
placed into the frontend's request bodies or URLs. Redis/provider code is unchanged.
These local checks cannot confirm that real backend bearer tokens, Vercel bypass
credentials, Redis credentials or LLM keys are absent from all hosted traffic.

## Exact proposed hosted update: separate approval required

Local branch remains `feat/streamlit-vercel-backend`, HEAD `e8a4415`.
Read-only remote verification found feature HEAD
`6898d936124ed45219b702f36c42db9bb6d3f29e`; its only change from local HEAD adds
`.devcontainer/devcontainer.json`. Main remains
`164fe226c95af6259d5f67170e1e20965d4c280b`. Remote objects were fetched locally
without moving local HEAD, pushing or changing any hosted resource.

The isolated review snapshot, nine-file SHA-256 manifest, scoped patch and test/scan
receipts are under ignored `.verification-local/summary-ui-review/`. The snapshot
is based on the remote parent, includes its devcontainer, and excludes unrelated
local changes. Only report text was finalised after its successful full suite;
tested Python hashes are checked against the final manifest.

After approval, publish only a reviewed nine-file correction based on `6898d93`,
preserving its devcontainer addition. Recheck remote HEAD and stop on divergence;
do not force-push or publish the existing unrelated index. Updating this feature
branch may automatically rebuild the existing Community Cloud app, so that push
is itself a deployment action requiring approval. Preserve private viewer access,
entrypoint `deployment/streamlit/app.py`, Python 3.12, dependency manifests and
all private server secrets. No new app, Vercel deployment, Production change,
provider change, credential rotation or paid resource is proposed.

Keep the protected permanent mocked backend `dpl_3XLLkftWMZQx7U8bJwjXJG6NraRt`.
Before declaring hosted verification complete, obtain explicit approval for a
bounded mocked acceptance run and use a browser tool capable of sanitised header
and decoded WebSocket inspection. Do not collect raw HARs, cookies or secret values
in a report. A future approval must set HTTP/admission caps; none were consumed
by hosted interview actions in this task.

## Rollback and remaining risks

Before publication, record the actual remote parent and approved correction SHA.
If the update fails, revert only that correction on the feature branch and rebuild
the existing private app, under the update approval. Preserve the devcontainer
commit and all earlier work; never reset or force-push the branch. Leave Vercel,
Redis, viewer settings and secrets unchanged. A rebuild may end active in-memory
sessions. If exposure is discovered, stop verification and obtain separately
scoped containment/rotation approval; no rotation is authorised here.

The hosted traffic gap remains a release blocker. Old blank takeaways can only be
backfilled while the corresponding feedback remains available; discarded earlier
text cannot be reconstructed. The corrections have not been tested on a newly
rebuilt hosted frontend. No push or deployment is authorised by this report.

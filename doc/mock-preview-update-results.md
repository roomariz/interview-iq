# Protected mock Preview update results

Completed 17 November 2026, 22:40 CET. All LLM responses were synthetic; no live inference.

## Deployment and provenance

- [Protected Preview](https://interviewiq-api-preview-14932zvli-roomas-projects.vercel.app)
- Deployment: `dpl_4ij7fmNGu3hb5ubUHrqrTMwk6wi9`; READY; target `null` (Preview); `fra1`.
- Owner/project: personal `roomas-projects/interviewiq-api-preview`, Hobby.
- Project ID: `prj_XjaA1iTvTn5AmtN8PCg551qeUGLg`.
- Repository/branch: `roomariz/interview-iq`, `feat/streamlit-vercel-backend`.
- Pushed only approved commits `53e5428` and `69e7d0c`; remote branch tip
  `69e7d0c8141524446012afea36c017b5c0965ee2`.
- Main remains `164fe226c95af6259d5f67170e1e20965d4c280b`; no merge.
- Source artifact: 104 files, 391,655 bytes, from Anonymous access controls commit with the reviewed
  permanent mock overlays. All 104 uploaded source hashes match the inventory.
- Inventory SHA-256:
  `fcb999dc082544a095a904ff06a5f4b5a48caa9a581d421e9c46705bedae1661`.
- Python 3.12; function maximum 300s; aggregate deadline 150s; no runtime-version
  or function-setting changes beyond the approved source update.

Vercel CLI rejects `--skip-domain` for Preview, so the executed command omitted
that Production-only option and retained explicit `--environment preview`.
The source/configuration safety checks passed before submission. Only one new
Preview was created; there was no retry as Production or domain promotion.
The CLI's rejected batch-variable input changed nothing; the five variables were
then added using individual secure stdin JSON requests, with read-back verification.

## Environment and protection

Exactly five variables were added, all Preview-only:

| Variable | Value |
| --- | --- |
| BACKEND_VISITOR_SIGNING_KEY | Independent 48-random-byte secret, stored as sensitive; value withheld |
| BACKEND_VISITOR_RATE_LIMIT | 10 |
| BACKEND_VISITOR_DAILY_LIMIT | 100 |
| BACKEND_GLOBAL_DAILY_LIMIT | 1000 |
| BACKEND_INGRESS_RATE_LIMIT | 300 |

All 15 original variable records, including secret IDs/ciphertexts/metadata, were
unchanged. Global 30/minute, distributed concurrency four, existing Redis and
namespace, dummy Ollama key, disabled fallback and other settings remain intact.
No live Google/xAI/OpenRouter key was added. No frontend deployment was performed.

All Deployments authentication remains enabled. Public health and invalid bypass
requests redirect to Vercel authentication; backend bearer and signed visitor
tokens are additionally required. Secrets stayed in private settings/header-only
clients; none appeared in source, commands, responses or inspected normal logs.

## Verification

| Check | Result |
| --- | --- |
| Exact local artifact isolation | Four provider paths blocked across Requests and sync/async HTTPX; Production, live keys and fallback refused |
| Uploaded source inventory | 104/104 hashes matched; no unrelated documentation, private settings or bytecode |
| Hosted platform/backend authentication | Missing/invalid platform bypass or bearer denied |
| Visitor authentication | Missing, forged and correctly signed expired identities denied with 401 |
| Mock workflows | Context, five-question generation, grounded evaluation/follow-up and example answer passed |
| Schema rejection | 422; no admitted-work counters debited |
| Synthetic provider outage | Controlled 502; raw error text withheld |
| Visitor minute | Exactly 10 admitted; next rejected; another identity can proceed |
| Visitor daily | Exactly 100 admitted; next rejected; 6 exhausted synthetic identities observed |
| Global minute | Exactly 30 admitted; fresh visitor rejected; Retry-After and natural reset verified |
| Global daily | Exactly 1,000 admitted across all verification activity; fresh identity rejected with long Retry-After |
| Ingress minute | 300; schema-invalid excess rejected 429, work counters unchanged |
| Hosted concurrency | Four held requests admitted; eight further hosted requests rejected 429 |
| Independent-instance concurrency | Two separate local exact-artifact processes sharing managed Redis also rejected while hosted capacity was full |
| Lease ownership | Wrong-owner release/renewal had no effect; busy denials did not debit work budgets |
| Lease renewal | All four hosted owned leases extended during active work |
| Deadlines and release | Four hosted 504s at 152.12s; leases released; independent instances recovered |
| Crash/expiry | Independent mock worker stopped; real managed lease retained until 330s expiry; expired owner could not renew |
| Logging | Python 3.12 build and retrieved runtime logs excluded configured credentials, Redis URL/hostname and synthetic input text |
| Complete offline suite, real local Redis | 636 passed; 11 live/e2e deselected; five existing warnings |
| Dependency audits from approved preparation | Backend 26, development 82, installed 96 packages; zero known vulnerabilities; pip check passed |
| Lint from approved preparation | Changed/new files passed; 35 existing whole-repository findings remain |
| Secret scans before publication/upload | Git history and exact artifact clean; redaction enabled |

The global daily run used 987 successful hosted
synthetic context requests in addition to the other admitted verification work.
No quota limits, clock, namespace or counters were reset/lowered to accelerate it.
The separate crash check required one retry to distinguish its persistent lease
from concurrent short-lived quota requests; no deployed code/settings changed.
An unexpected host-time interruption stopped the first bounded quota loop at 489.
Protection/configuration/bootstrap were rechecked before resuming from that same
managed counter and daily window. No counters were reset or limits changed.
The original full-suite network guard remained active; no provider was contacted.

## Bootstrap and remaining limits

The only Production record remains inert bootstrap
`dpl_3r1dLtGUkZZ38R352icSbajiBTLx`. Its creation time, fixed body hash, READY status,
empty aliases and protected access are unchanged. Authorised health still returns
503 with `X-InterviewIQ-Bootstrap: inert`. Project resources and Hobby plan match
the pre-deployment snapshot; there are exactly three deployment records.

The deliberate daily-cap test leaves the Preview's 1,000/day allowance exhausted
until approximately **18 November 2026, 15:51 CET**, when its existing
window expires naturally. Health remains available through authorised protection.
Counters were not cleared. Anonymous session resets cannot bypass that global cap.

This remains a protected synthetic Preview. No live-provider quality, latency,
cost, public abuse resistance or hosted Streamlit integration is established.
Request quotas are not token/spending limits; anonymous session resets remain
possible. Platform logs are outside application redaction control; the retrieved
build/runtime output was inspected privately. No paid resources were provisioned.

Reports/private diagnostics remain local. Earlier uncommitted documentation was
preserved, excluded from the artifact and not pushed. Stop here; live-provider
testing, public release and any further deployment require separate approval.

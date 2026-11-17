# Phase 4B protected mocked Preview: approval proposal

17 November 2026. Preparation only; no push, deployment or cloud mutation performed.
Phase 4A local commit: `53e54283d2ea42bc7cb544a24f6fecaef230989c` on
`feat/streamlit-vercel-backend`. Main was not merged or modified.

## Verified existing project

- Owner: `roomas-projects`, team `team_zoD1onU2GTJgvvZfKmwLnP0d`, Hobby.
- Project: `interviewiq-api-preview`, ID `prj_XjaA1iTvTn5AmtN8PCg551qeUGLg`.
- Fresh read-only CLI checks confirm `ssoProtection.deploymentType=all`,
  `autoAssignCustomDomains=false`, Fluid, fixed basic build machine, `fra1`, 300s.
- Existing application variables are all Preview-only; no live provider key
  variables exist for Google, xAI or OpenRouter. The Ollama key is the dummy below.
- The only Production record remains inert bootstrap
  `dpl_3r1dLtGUkZZ38R352icSbajiBTLx`, READY, with no aliases. Unauthenticated health
  returns 302 to authentication; the stored bypass returns fixed 503 with
  `X-InterviewIQ-Bootstrap: inert`. No application is proposed for Production.
- Existing mocked Preview is `dpl_HsLPNmGGtrPpQum5na4mSHHfpbBF`.
- Connector reads failed for this owner; scoped existing CLI authentication
  succeeded. No account/connector permissions were changed.

## Exact proposed Preview environment

All rows target **Preview only**, without branch overrides. Preserve existing
secret records and the automation protection bypass. Do not copy into Production.

| Variable | Value | Action |
| --- | --- | --- |
| APP_ENV | production | Preserve; enables production safeguards within Preview |
| LLM_PROVIDER | ollama | Preserve |
| OLLAMA_HOST | https://ollama.com | Preserve; requests are permanently intercepted |
| OLLAMA_MODEL | gemma4:cloud | Preserve; synthetic metadata only |
| OLLAMA_API_KEY | mock-only-not-a-real-provider-key | Preserve dummy |
| OLLAMA_FALLBACK_TO_OPENROUTER | false | Preserve |
| LLM_TIMEOUT | 60 | Preserve |
| BACKEND_REQUEST_DEADLINE | 150 | Preserve |
| BACKEND_RATE_BACKEND | redis | Preserve |
| BACKEND_RATE_NAMESPACE | interviewiq-mocked-preview | Preserve |
| BACKEND_RATE_LIMIT | 30 | Preserve global minute cap |
| BACKEND_MAX_CONCURRENT | 4 | Preserve value; now distributed across instances |
| BACKEND_API_SECRET | Existing sensitive value | Preserve unchanged |
| UPSTASH_REDIS_REST_URL | Existing sensitive value | Preserve unchanged; never print |
| UPSTASH_REDIS_REST_TOKEN | Existing sensitive value | Preserve unchanged |
| BACKEND_VISITOR_SIGNING_KEY | New independent random secret, at least 32 random bytes | Add as sensitive, generate privately after approval |
| BACKEND_VISITOR_RATE_LIMIT | 10 | Add |
| BACKEND_VISITOR_DAILY_LIMIT | 100 | Add |
| BACKEND_GLOBAL_DAILY_LIMIT | 1000 | Add |
| BACKEND_INGRESS_RATE_LIMIT | 300 | Add |

The signing key must differ from the backend API secret. Install the same value
only in the trusted Streamlit server's private settings if testing that frontend;
otherwise the verification client mints signed synthetic visitor tokens privately.
Do not deploy the frontend as part of this backend Preview update. Older clients
without signed identities cannot use the updated backend.

The [Phase 4A proposal](phase4a-preview.md) matches the code: visitor 10/minute and
100/day; global 30/minute and 1,000/day; ingress 300/minute; concurrency four.
Minute/day windows expire 60s/24h after opening, rather than at calendar boundaries.
Atomic admission acquires a random owned lease and debits all four work quotas.
Denials do not debit work quotas. Redis failure returns 503 without memory fallback.
Redis TIME controls leases: 330s lifetime, renewal every 30s, owner-only release;
expired leases cannot be renewed. Timed-out local transports retain their leases
until they exit. The unchanged 300s function ceiling remains below lease expiry.
New `v4` quota keys start fresh counters; do not expose mixed backend revisions.

## Exact deployment change proposed

Publish the reviewed branch only after approval, then create **one new Preview**
from the derived backend-only mock artifact. Preserve Python 3.12, `fra1`,
`maxDuration=300`, existing dependency pins, disabled automatic Git deployments,
All Deployments authentication, bypass, aliases and project settings.
No provisioning, paid options, bootstrap update, promotion or domain assignment.

Local artifact: `.phase4a-local/phase4b-mocked-preview`; 104 source files,
391,655 bytes. Inventory SHA-256 (canonical sorted compact JSON of file hashes):
`fcb999dc082544a095a904ff06a5f4b5a48caa9a581d421e9c46705bedae1661`.
The ignored inventory is `.phase4a-local/phase4b-artifact-manifest.json`.
Application sources come from the Phase 4A commit, with these reviewed overlays:

1. `api/index.py` installs the permanent mock before application imports.
2. `requirements.txt` uses the committed backend-only requirements.
3. Existing hash-verified `preview_fixture.py` and `preview_questions.json`.

The artifact includes the new admission, identity and private logging modules.
It contains no frontend, tests, private settings, credentials or generated bytecode.
The fixture refuses Production, unexpected keys/providers and enabled fallback.
Requests is blocked except the synthetic Ollama interceptor; sync/async HTTPX
permits only POST to the configured Redis origin. All four provider paths were
verified blocked. Mocking is permanent; no environment toggle enables live calls.

Draft commands, **not executed**; run from the repository root after approval:

```powershell
git push origin HEAD:feat/streamlit-vercel-backend
node .npm-cache/_npx/6e2da5dc676fb619/node_modules/vercel/dist/vc.js deploy `
  .phase4a-local/phase4b-mocked-preview `
  --project prj_XjaA1iTvTn5AmtN8PCg551qeUGLg --scope roomas-projects `
  --environment preview --regions fra1 --skip-domain `
  --meta sourceCommit=53e54283d2ea42bc7cb544a24f6fecaef230989c `
  --meta sourceBranch=feat/streamlit-vercel-backend --meta mockOnly=true `
  --yes --non-interactive --no-wait --json
```

Before upload, recheck branch, commit, complete artifact inventory, protection,
owner/Hobby plan and unchanged bootstrap. Set only the five proposed variables
through secure stdin/API bodies; never put secrets into process arguments/chat.
After creation, require `target=null` and `VERCEL_ENV=preview`. Stop on any
Production classification or unexpected configuration; never retry as Production.

## Verification refreshed during preparation

| Check | Result |
| --- | --- |
| Complete default automated suite with disposable Redis 8.10.2 | 636 passed, 11 live/e2e deselected, five existing warnings |
| Two independent backend processes, capacity two | 12 simultaneous requests: two admitted, ten 429 |
| Real Redis ownership/renewal/expiry and quota tests | All five passed within complete suite |
| Backend manifest dependency audit | 26 packages, zero known vulnerabilities |
| Development manifest audit | 82 packages, zero known vulnerabilities |
| Installed environment audit | 96 packages, zero known vulnerabilities |
| pip check | No broken requirements |
| Changed/new Python lint and mock fixture lint | Passed |
| Whole repository lint | 35 existing findings, all in unchanged files |
| Gitleaks working source and reachable Git history | Zero findings; redaction enabled |
| Configured private credential comparison against source | Passed; values not printed |
| Derived artifact secret scan | Zero findings |
| Derived artifact synthetic workflow and safety checks | Four routes, signed auth, grounded evaluation, 504, controlled 502, blocked provider transports and Production refusal passed |
| Application logging privacy | URLs, bearer/header/body/CV and exception strings withheld; status/duration retained |
| Whitespace and selected source/document sizes | Passed; each at most 250 lines |

Private diagnostics/build products remain ignored under `.phase4a-local/`.
Earlier Phase 3B documents and ownership-history edits were present before this
task and remain preserved outside the Phase 4A commit. No secrets or unrelated
changes were included in that commit; the full working tree is not clean.

## Post-approval verification boundary

Use synthetic inputs, the existing Redis namespace and the approved numeric caps.
Verify platform/backend/visitor authentication, two visitor allowances, global
limits, Retry-After, cross-instance concurrency, timeout/release behaviour and
private runtime logs. Recheck bootstrap/protection after deployment. No temporary
quota changes, alternate Redis namespace, cloud failure injection or new resources
are proposed; approve those separately if needed. Local tests prove the Lua and
multi-process behaviour, not newly hosted Phase 4B behaviour. Platform-generated
logs require private hosted inspection; application redaction cannot control them.
Do not enable live inference or describe request quotas as token/spending limits.

Approval requested: push the reviewed branch, add the five Preview-only variables,
and deploy/verify this exact protected mocked Preview artifact. Production,
main, live providers, existing secrets and paid services remain outside approval.

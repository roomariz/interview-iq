# Protected mock Preview and bootstrap results

17 November 2026. Status: **protected mock Preview READY and verified**.

[Protected Preview](https://interviewiq-api-preview-2e5ivsxh5-roomas-projects.vercel.app)
under [roomas-projects/interviewiq-api-preview](https://vercel.com/roomas-projects/interviewiq-api-preview).
The user approved one inert protected Production-classified bootstrap to overcome
the first-deployment rule. InterviewIQ itself is deployed only to Preview.
No live LLM requests, paid services/upgrades, main merge or new Git push occurred.

## Git and source provenance

- Repository/branch: public roomariz/interview-iq, feat/streamlit-vercel-backend.
- Published source: `bf445983c4d5e192dc86bb74b4436c962c1ddb7b`.
- Prior security commit: `014f06b80d5ff10f485cd412965c8f49771d58a1`, preserved.
- Main remains `164fe226c95af6259d5f67170e1e20965d4c280b`.
- Publication review scanned 302 files, nine reachable commits and 425 historical
  blobs; no configured credentials or recognised credential patterns were found.
- The approved derived mock artifact contains 99 files, 377,034 source bytes;
  upload dry-run and SHA-256 checks matched the reviewed inventory.
- Manifest SHA-256: `22b6960988e60d2dc32345eda302bf2bcb23a2853cf92c8fd18cc51a2a7ea2c7`.
- Overlays: api/index.py imports the permanent mock transport; backend-only
  requirements.txt, preview_fixture.py and preview_questions.json are included.
  All other application files match the published commit byte-for-byte.
- No scoring, prompts, model rankings, API contracts or existing application source
  was changed. This hosted fixture is not a byte-identical release of the Git tree.
- Local documentation/ownership updates remain uncommitted and unpushed.

## Ownership, protection and bootstrap preflight

CLI 65.17.0 confirmed user roomariz-4797 is OWNER of personal roomas-projects,
team `team_zoD1onU2GTJgvvZfKmwLnP0d`, plan Hobby. The forbidden former workspace
was not used. Project ID: `prj_XjaA1iTvTn5AmtN8PCg551qeUGLg`.

Before bootstrap execution, fresh API reads verified:

- All Deployments Vercel Authentication: ssoProtection.deploymentType=all.
- Automatic custom production-domain assignment disabled.
- No trusted-IP, trusted-source or OPTIONS allowlist exceptions.
- Exactly one automation bypass, matching the approved privately stored secret.
- All 15 application variables Preview-only; no Production application variables.
- Hobby ownership and fixed basic build machine, with no paid additions.

The existing unassigned domain returned 404 before execution. That was evidence
of no deployment, not an authentication challenge. Configuration/scope were
verified before execution; actual generated-URL authentication was tested
immediately after the inert record existed and before deploying InterviewIQ.
[All Deployments protection](https://vercel.com/docs/deployment-protection#all-deployments)
protects production and Preview domains and is included on Hobby.

## Inert bootstrap: the only Production-classified record

- ID: `dpl_3r1dLtGUkZZ38R352icSbajiBTLx`; target production; READY.
- Built-output upload: two files, 343 bytes, no build step or dependencies.
- Contents: routing configuration and fixed inert text; every authorised route
  returns 503 with marker X-InterviewIQ-Bootstrap=inert.
- No application code, functions, provider transport or secrets in the upload.
- Deployment used --prebuilt --prod --skip-domain against the exact personal project.
- Returned aliases list is empty. API aliasAssigned=true does not imply an alias
  exists; the stable interviewiq-api-preview.vercel.app domain still returned 404.
- Unauthenticated generated-URL root and /api/health requests returned 302 to
  Vercel authentication. Approved bypass returned only the fixed inert 503 text.
- The first strict body comparison differed only by CRLF; line-ending normalisation
  confirmed the full expected text. No redeployment or protection weakening was needed.

No InterviewIQ application was released or promoted to Production.

## Preview build and packaging

| Item | Observed result |
| --- | --- |
| Deployment | dpl_HsLPNmGGtrPpQum5na4mSHHfpbBF |
| Environment | target=null (Preview), READY |
| Region | fra1; runtime log records also show Frankfurt |
| Python | Build logs explicitly select Python 3.12 from pyproject.toml |
| Dependency discovery | Backend-only pyproject installation; no custom install/build/output overrides |
| Build | Build Completed log reports 8 seconds; API build-to-ready interval 16.23 seconds |
| Function configuration | api/index.py, maxDuration=300, reviewed exclusions retained |
| Application deadline | 150-second aggregate budget tested on hosted API |
| Git provenance metadata | sourceCommit=bf445983..., sourceBranch=feat/streamlit-vercel-backend, mockOnly=true |
| Production aliases | No promote or custom-domain assignment; Preview aliases list empty |
| Final deployment count | Two: one inert Production bootstrap, one mock Preview |

A build and working routes establish observed hosted compatibility. Exact final
dependency-bundle bytes were not exposed by the inspected metadata; 377,034 bytes
is source size, not the dependency bundle size. No claim of sustained-load,
regional failover or real-provider quality/cost follows from this build.
The current project is GitHub-linked to roomariz/interview-iq with main as its
production branch. The reviewed source disables automatic Git deployments;
no Git branch or repository setting was changed during bootstrap verification.

## Hosted functional verification

| Check | Result |
| --- | --- |
| Public Preview health without bypass/cookies | 302 to Vercel login; ordinary public access denied |
| Invalid protection-bypass value | Denied by Vercel protection |
| Protected authorised health | 200, status=ok |
| Missing backend bearer | 401 |
| Invalid backend bearer | 401 |
| Authenticated context / Redis connectivity | 200 |
| Mocked question route | 200; exactly five schema-validated questions |
| Mocked evaluation route | 200; grounded pipeline, scores, trust and follow-up validated |
| Mocked example-answer route | 200; expected synthetic text |
| Invalid answer length | 422, controlled validation response |
| Synthetic provider outage | 502 after bounded retry/error path; raw synthetic provider text withheld |
| Hosted aggregate deadline | 504 after 150.05 seconds |
| Redis empty-window quota | Sequential 31 synthetic context requests: 30 x 200, one 429 |
| Retry-After | 59 seconds on the observed 429 |
| Quota expiry/reset | 200 after the reported wait plus one second |
| Credential response checks | No configured secret/token values found in checked bodies; final headers also checked |

The quota run waited beyond prior usage, used the dedicated
interviewiq-mocked-preview namespace and allowed natural expiry. No unrelated
Redis keys were read/deleted, and no Redis service was provisioned or reconfigured.
The hosted admission check was sequential; the earlier two-process atomic
concurrency, invalid-token and outage passes remain local evidence. The historical
unexplained Redis assertion is not retroactively explained by these passes.

The mock artifact permanently intercepts Ollama responses and guards requests/httpx
provider networking; only the configured Redis origin may use actual HTTP.
It requires its explicit dummy Ollama key, refuses other provider keys and rejects
Production execution. Live model names in synthetic metadata/logs do not imply
real inference. No live LLM call was performed.

## Security findings and remaining limits

- All Deployments protection remains enabled after both deployments. Ordinary
  generated-URL access was denied; the unassigned stable domain serves no app.
- Backend secret and Redis credentials were passed securely via stdin into
  sensitive Preview variables. They were not placed in process arguments/source.
  Preview variables were not copied into Production. Private state is Git-ignored.
- Build-log scan found no configured secret/token values. Runtime-log review also
  found no backend secret, Redis token or automation bypass secret.
- Runtime HTTPX INFO records include the Redis endpoint URL/hostname. This is
  operational metadata in access-controlled logs, not a credential, but it is a
  privacy limitation. Consider redacting/suppressing transport endpoint INFO logs
  in a separately reviewed change; the published application was not changed here.
- Python runtime/development/installed audits were clean in the preceding phase;
  no runtime dependency pins changed in this phase. The published mocked suite
  baseline remains 607 passed, zero failed, 11 deselected; it was not rerun here.
- Existing whole-repository lint debt is 35 findings. The mock fixture lint passed.
- Current limits remain shared 30 requests/minute and four concurrent requests per
  process. They do not provide visitor fairness or a distributed concurrency cap.
  [Anonymous quota design](anonymous-rate-limit-proposal.md) remains assessment-only.
- Live-provider quality, latency, cost, sustained hosted concurrency, real Redis
  outage behaviour on Vercel and hosted Streamlit integration remain unverified.
- Vercel account 2FA was not changed; the earlier owner-action recommendation remains.

Next: keep this protected mock Preview for review. Before public release, approve
visitor/global budgets and distributed concurrency, address endpoint-log privacy,
review CI's Python 3.11 setting, and separately authorise live-provider measurements.
No further deployment, promotion, paid resource or live inference is authorised by
this report. The requested protected Preview verification is complete.

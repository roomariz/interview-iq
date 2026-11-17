# Phase 3B Preview proposal — Redis verified; ready for approval

The user explicitly approved retaining public source repository
`roomariz/interview-iq`. Do not change its visibility. Public source does not make
provider keys or deployment secrets public. No deployment or infrastructure
configuration has been performed. Only expiring Redis verification counters were written.

## Proposed project configuration

| Item | Proposed value |
| --- | --- |
| Vercel team | astraut-solutions' projects (`astraut-solutions-projects`) |
| New project name | interviewiq-api-preview |
| Source | existing roomariz/interview-iq repository |
| Publication branch | codex/phase3b-preview, based on feat/streamlit-vercel-backend |
| Root / framework | repository root / FastAPI |
| Entrypoint | api.index:app, via tool.vercel.entrypoint |
| Python | 3.12 |
| Function duration | 300 seconds; aggregate API deadline 150 seconds |
| Region | fra1 (Frankfurt), matching user-confirmed Upstash eu-central-1 |
| Target | Preview only, with deployment protection retained |
| Dependencies | backend-only pyproject pins; frontend/deployment folders excluded |
| Install settings | FastAPI preset automatic installation; backend pyproject manifest |
| Build / output directory | preset defaults; no custom command or static output directory |
| Automatic Git deployments | disabled by git.deploymentEnabled=false; explicit Preview only |
| Provider | Ollama Cloud; gemma4:cloud alias; OpenRouter fallback disabled |
| Rate limiting | managed Upstash REST; shared interviewiq-preview namespace |

The reviewed preparation commit is based on `83c43f6` and is prepared locally on
`codex/phase3b-preview`. Publication remains unapproved. Obtain its exact revision
with `git rev-parse codex/phase3b-preview` before an approved push/deployment.
Remote branch inspection found no existing `codex/phase3b-preview`; main is
`164fe22`, and the remote feature branch remains `83c43f6`. No force-push or merge
is proposed. See [publication plan](phase3b-publication-plan.md) for commit scope.
The GitHub connector reports read access without push/admin permissions; an
approved push will require authorised Git transport/account access.

No InterviewIQ project was found among the connected Vercel team's projects.
Project creation, Git connection, environment changes and Preview deployment have
not run. Review this configuration after Redis passes, then obtain the requested
approval before these external changes. Do not trigger a Git import that silently
creates the first Production deployment; use an explicit Preview deployment and
leave production domains/releases unassigned. Do not enable automatic Production
deployments from main during this phase.

## Backend and frontend templates

- `deployment/vercel-preview.env.example`: backend Preview variable names,
  placeholders, Ollama settings, quotas, Redis and deadlines.
- `deployment/streamlit/secrets.example.toml`: server-side frontend settings only.
- `deployment/streamlit/app.py`: Community Cloud entrypoint; calls the unchanged
  existing application main function.
- `deployment/streamlit/requirements.txt`: references the frontend-only pins.

Community Cloud searches the entrypoint directory before the repository root.
The dedicated frontend manifest prevents discovery of the backend pyproject or
the combined local requirements. Choose Python 3.12 explicitly and the approved
Preview source branch. Keep the existing root entrypoint for local use.
[Streamlit dependency discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

Protected Vercel Preview URLs require an automation bypass header for server-side
Streamlit requests. The client now optionally reads
`VERCEL_AUTOMATION_BYPASS_SECRET` and sends `x-vercel-protection-bypass` in the
request header, alongside the existing backend bearer secret. Redirects remain
disabled. Neither secret enters the request body or browser state.
Configure the bypass in Vercel's deployment-protection settings and enter its
secret in Streamlit's secure settings. Do not disable Preview protection just to
make requests succeed.
[Official bypass documentation](https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation).

Sources: [Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Python runtime](https://vercel.com/docs/functions/runtimes/python),
[Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Gates before deployment

The publication-time dependency audit reported advisories in five packages.
The historical [audit](phase3b-publication-plan.md) is preserved; the subsequent
[security review](dependency-security-review.md) records the patched pins and
clean current audits. Existing functional failures and hosted checks remain gates.

1. Real Upstash verification passed across two independent backend processes.
   See [the actual verification results](phase3b-redis-verification.md). Repeat quota
   and failure checks against Vercel after deployment.
2. Review and publish a secret-free source revision to the approved repository
   through an authorised account. Confirm the exact commit before deployment.
3. Approve the exact project/team/branch/configuration and create Preview only.
4. Verify build, bundle, routing, auth, Redis, sizes and errors. Current health is
   public liveness; authenticated context is the no-LLM protected readiness check.
5. Run a hosted mocked interview workflow using an isolated test build with
   test fixtures injected, without introducing a remotely selectable public mock
   provider into the production application. This build has not been prepared or
   deployed; local mocked workflow checks do not count as hosted verification.
6. Configure/deploy the Streamlit test app only after backend Preview passes.
7. Request a small explicit live Ollama test budget before inference. Measure real
   latency, retries, model-call counts and costs; do not assume the alias is free.
8. Assess the 12 known failures for release impact. Production is not recommended
   until hosted workflow, real latency, security and cost gates have passed.

## Required Preview environment variables

Set these in Vercel **Preview only**; no secret values are stored in this proposal.
The committed example is `deployment/vercel-preview.env.example`.

| Variables | Values / secure source |
| --- | --- |
| APP_ENV / LLM_PROVIDER | production / ollama |
| OLLAMA_MODEL / OLLAMA_HOST | gemma4:cloud / https://ollama.com |
| OLLAMA_FALLBACK_TO_OPENROUTER | false; OpenRouter key unnecessary while disabled |
| OLLAMA_API_KEY | existing provider credential, entered securely |
| BACKEND_API_SECRET | generate a random secret of at least 32 bytes; share only with Streamlit server |
| UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN | existing verified database's HTTPS REST URL and write-capable token |
| LLM_TIMEOUT / BACKEND_REQUEST_DEADLINE | 60 / 150 seconds |
| BACKEND_RATE_BACKEND / BACKEND_RATE_NAMESPACE | redis / interviewiq-preview |
| BACKEND_RATE_LIMIT / BACKEND_MAX_CONCURRENT | 30 per minute shared / 4 per instance |

APP_ENV=production enables strict API security; the deployment target remains
Preview. Vercel supplies its own VERCEL/VERCEL_ENV system variables; do not set
them manually. Keep project install/build overrides unset and inspect the actual
build to confirm backend-only dependency discovery. No cloud build has run yet.

## Vercel actions requiring the user's account or approval

- Approve project/team/branch/configuration and Git publication separately.
- Authorise Vercel's GitHub integration for the existing public repository.
- Create/configure the project without triggering an initial Production import;
  explicitly select Preview for any later deployment. No domains or promotion.
- Enter backend secret values securely in Preview environment settings. Do not
  paste them into chat or commit local dotenv files.
- Confirm Frankfurt, Python 3.12, Fluid Compute and the 300-second function budget
  are available on the current plan; do not upgrade or enable paid extras.
- Retain Preview protection. Create an automation bypass secret in Vercel's
  protection settings for the Streamlit server; keep it out of source/browser UI.

`git.deploymentEnabled=false` disables automatic Git-triggered deployments in
this reviewed source; an explicit later deployment still requires selecting the
Preview target. It does not protect other revisions that lack that setting.
[Official Git configuration](https://vercel.com/docs/project-configuration/git-configuration).

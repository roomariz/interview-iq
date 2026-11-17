# Phase 3A/3B Git publication plan

Prepared on 16 November 2026. No push, project creation, deployment, paid service
or live LLM request is authorised by this preparation step.

## Local commit and target

- Source repository: public `roomariz/interview-iq`.
- Parent: `83c43f6`, the published `feat/streamlit-vercel-backend` revision.
- Prepared local/publication branch: `codex/phase3b-preview`.
- Commit title: `feat: prepare Phase 3A and 3B for Vercel Preview`.
- Scope: aggregate request deadlines, bounded provider retries, atomic shared Redis
  quotas, production configuration, separate dependency manifests, Preview bypass
  support, Streamlit Cloud entrypoint, verification tooling, tests and documentation.
- Scoring weights, evaluation prompts, existing tests and provider rankings remain
  unchanged. Existing frontend screens and Streamlit session ownership remain.

The remote branch-name check found main at `164fe22` and the existing feature
branch at `83c43f6`. No remote `codex/phase3b-preview` branch existed at inspection.
This new branch retains the existing Phase 2/branding/confidence ancestors; it
does not merge them into main. Only one new preparation commit is added to the
existing feature tip. No force push, main update or merge is proposed.

After approval, the proposed publication command is:

```powershell
git push --set-upstream origin codex/phase3b-preview
```

Do not execute it without explicit user approval. Recheck the remote branch and
local commit before publishing. The GitHub connector currently reports read-only
repository access; any push requires an authorised Git transport/account. A
successful read of the public repository does not prove write permission.

## Secret and artefact review

The candidate changes were scanned for exact values of locally configured API
keys, Redis credentials, backend/bypass secrets and common credential formats.
No matches were found. Only placeholder `.env.example` and deployment templates
belong in the commit. Actual `.env`, Streamlit secrets, Vercel state, virtual
environments, audit/test output, downloaded wheels and caches remain ignored.
The staged tree receives a second secret/path check before committing.
These checks are scoped evidence, not a guarantee against every possible secret
format or sensitive document in all historical revisions.

## Verification and dependency audit

- Fresh full mocked suite: 587 passed, 12 existing failures, 11 deselected,
  34.81 seconds; no new failing identities versus the Phase 3B baseline.
- New Phase 3A/3B checks: 33 passing tests in the full suite.
- Real Redis: previously passed two-process combined quota, concurrency, auth,
  Retry-After, simulated outage and invalid-token fail-closed verification.
- Changed Python files: lint must pass before commit; whitespace, manifest and
  250-line checks are also required.

The required pip-audit run is **not clean**. It audited the union of deployed
backend/frontend requirements and reported 100 advisory entries in five packages.
Removing duplicate identical package/advisory IDs leaves 71 distinct ID pairs;
aliases may still describe the same underlying vulnerability. These figures must
not be presented as 100 distinct vulnerabilities or a passed security audit.

| Package | Audited version | Distinct advisory IDs | Reported fixed versions |
| --- | --- | --- | --- |
| python-dotenv | 1.0.1 | 1 | 1.2.2 |
| requests | 2.32.3 | 2 | 2.32.4, 2.33.0 |
| streamlit | 1.40.0 | 2 | 1.53.1, 1.54.0 |
| pillow (frontend transitive) | 11.3.0 | 59 | 12.1.1 through 13.0.0 across findings |
| starlette (backend transitive) | 0.41.3 | 7 | 0.47.2 through 1.3.1 across findings |

Fixed versions above are advisory data, not a validated upgrade recommendation.
FastAPI/Starlette constraints and Streamlit dependencies need coordinated review.
No versions were upgraded during Git preparation. Findings require triage and
remediation before deployment approval; local commit creation does not approve
deployment. The existing 12 test failures also remain release review gates.
Full audit JSON/output remains in ignored `.pytest_cache/phase3-publication-audit.*`.

## Vercel Preview configuration and user actions

See [the complete proposal](phase3b-proposal.md) for Preview environment variables.
The proposed project is `interviewiq-api-preview` under
`astraut-solutions-projects`, using repository root `.`, FastAPI `api.index:app`,
Python 3.12, `fra1` Frankfurt, a 300-second function budget and 150-second API
deadline. Frankfurt matches the user's Upstash `eu-central-1` selection.

Use the FastAPI preset defaults for dependency installation/build/output, with
backend dependencies declared in pyproject. Inspect actual build output before
accepting packaging; no Vercel build has run. `git.deploymentEnabled=false`
disables automatic Git-triggered deployments for this reviewed revision.
Later deployment must still explicitly target Preview.

The user's Vercel account must authorise the repository integration, confirm the
existing plan/region/Fluid settings, enter secrets in Preview-only environment
settings and configure Preview protection/automation bypass for Streamlit.
Avoid an initial Production import and do not assign production domains, promote
a release, upgrade a plan or create paid resources. Git publication approval is
separate from approval to create/configure/deploy the Vercel project.

## 17 November security follow-up

The historical advisory results above are preserved. [The remediation review](dependency-security-review.md) records patched pins, clean current audits and the unchanged failure baseline. Security changes are prepared locally; publication remains unapproved.

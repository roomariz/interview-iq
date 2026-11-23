# Protected Preview deployment investigation

Historical investigation before the user approved a protected inert bootstrap.
The subsequent bootstrap and Preview results are in [the execution report](protected-mock-preview-results.md).

**Recommendation:** no officially supported Preview-first path was established for
this zero-deployment project. Keep `interviewiq-api-preview` undeployed under the
current prohibition on any Production deployment. Prefer a separately approved,
dedicated, previously initialised project in `roomas-projects`, or obtain written
Vercel clarification of a Preview-first exception before any deployment request.

This investigation executed no deployment, file upload, project/environment update,
Git mutation, live LLM request or paid-service operation. Cloud checks were GET-only.
Published application commit remains `bf445983c4d5e192dc86bb74b4436c962c1ddb7b`.

## 1. Current account/project evidence

The authenticated CLI confirms `roomariz-4797`, OWNER of `roomas-projects`, Hobby.
Project: `interviewiq-api-preview` / `prj_XjaA1iTvTn5AmtN8PCg551qeUGLg`.
Read-only API checks returned:

| Item | Observed state |
| --- | --- |
| Deployments / project targets | Zero deployments; no configured target deployments |
| Protection | ssoProtection.deploymentType=all_except_custom_domains (Standard) |
| Auto-assign custom domains | false |
| Project domain | interviewiq-api-preview.vercel.app; no branch/custom-environment assignment |
| Framework / function settings | FastAPI, Fluid, fra1, 300 seconds, fixed basic build machine |
| Application variables | 15; every target is Preview only |
| Sensitive variable metadata | Backend secret and Redis URL/token marked sensitive |
| Git link currently present | GitHub roomariz/interview-iq; productionBranch=main |

The Git link is present in the current read; the earlier execution report recorded
it absent at initial setup. This investigation neither connected nor altered it.
A Git connection alone does not initialise deployment history. The repository's
reviewed configuration disables automatic Git deployments; no push was performed.

Secret values were not retrieved or displayed. Existing mock-only configuration,
Preview secret records and Redis isolation were not changed. Local artifact hashes
are checked separately below; local evidence is not a hosted test result.

## 2. Latest CLI and API documentation

The official npm registry reports **Vercel CLI 65.17.0**, matching the installed
version. Only version/help/source inspection ran; no deploy command ran in this
investigation. The current documented selector is `--environment=preview`;
`--target=preview` appears explicitly in the first-deployment documentation.
[CLI reference](https://vercel.com/docs/cli/deploy).

The [environment reference](https://vercel.com/docs/deployments/environments#first-deployment)
expressly covers dashboard imports, CLI deployments, explicit Preview selection
and non-production Git branches. It defines the first deployment by absence of
prior deployment records, including failed/cancelled records. Deleted records do
not count. A rejected request which creates no record does not initialise a project.
Thus the earlier refusal did not initialise this project. First deployments use
Production variables; Preview-only secrets do not become available automatically.

The [REST creation reference](https://vercel.com/docs/rest-api/deployments/create-a-new-deployment)
says omitting `target` defaults to Preview; response `target=null` indicates Preview.
However, it provides no explicit zero-history exception to the first-deployment
rule. It documents `staging`, `production` and custom identifiers rather than a
special first-Preview override. No POST was sent to resolve this documentation gap.
Do not interpret the generic default as a supported bypass of the lifecycle rule.

## 3. Does this affect only the previous command?

| Method | Finding |
| --- | --- |
| Current CLI source upload | Guard checks for any prior deployment and refuses an explicit non-Production first target; matches the earlier first_deployment_production result |
| CLI --prebuilt | Same non-Production first-deployment guard; prebuilding is not a bypass |
| Dashboard Git import | Explicitly covered by the official first-deployment rule |
| Non-main branch / PR workflow | The environment documentation makes first deployment the exception to ordinary Preview routing |
| Direct REST / SDK / connector | No documented first-Preview exception; wrapper/default target descriptions cannot establish one; not experimentally tested |
| --skip-domain / disabled auto-assignment | Controls domain promotion, not environment classification or the environment-variable scope |
| Temporary deployment | Official CLI reference says temporary deployments target Production; unsuitable |
| Custom staging environment | Pro/Enterprise feature, outside this Hobby/free-tier scope; no established first-deployment exemption |

This is documented as a project lifecycle rule, not just a limitation of the last
CLI spelling. The installed CLI applies its guard independently of source/prebuilt
packaging and whether the selected project already exists. We did not empirically
prove every backend entrypoint behaves identically; doing so would require creating
deployments, which this investigation prohibits. No unsupported workaround is proposed.

## 4. Protection and Production domain exposure

[Standard Protection](https://vercel.com/docs/deployment-protection#standard-protection)
protects Preview and unique generated deployment URLs, including unique Production
deployment URLs. Production domains remain exempt. The API enum's name
`all_except_custom_domains` must not be read as a guarantee that a project's
stable `*.vercel.app` production domain is private. The current unbranched project
domain is a potential Production serving address; zero deployment records mean
no application deployment currently exists behind it.

`autoAssignCustomDomains=false` and `--skip-domain` withhold domain promotion;
they do not turn a Production build into Preview. Standard Protection alone is not
a public-exposure guarantee for a first Production bootstrap. Check every alias,
production domain, redirect, exception and bypass before asserting privacy.
[CLI Skip Domain documentation](https://vercel.com/docs/cli/deploy#skip-domain).

Vercel documents [All Deployments protection](https://vercel.com/docs/deployment-protection#all-deployments)
as covering production domains as well as Preview/unique URLs. The corresponding
API setting is `ssoProtection: {"deploymentType":"all"}`.
[Authentication API settings](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication#how-to-manage-vercel-authentication-with-the-api).
Both that scope and Vercel Authentication are included on Hobby, without a paid
add-on. [Current protection pricing](https://vercel.com/docs/deployment-protection/usage-and-pricing).
No protection setting was changed here. Automation bypass secrets still grant
access to authorised test clients and must remain private/header-only.

## 5. Can the current project be initialised without public Production traffic?

**Without any Production classification:** no supported route was established.
Under the current constraints, leave the project uninitialised.

**With a private Production record:** a separately approved bootstrap could enable
All Deployments authentication before any build, verify its effective scope, keep
aliases unpromoted, and use an inert no-secret/no-provider bootstrap. It remains
Production even if protected, unpublished to stable domains or deliberately failed.
It is not authorised by the existing Preview-only approval and was not attempted.
Existing Preview variables should remain Preview-only, never copied into Production.
The approved InterviewIQ mock artifact also rejects Production execution; do not
weaken that guard to initialise the project.

The environment reference says a failed first record can allow subsequent previews
without a successful Production site. This explains a possible no-public-app
bootstrap, not an exemption from the ban on Production deployment records. An
intentionally failed/cancelled first deployment is still outside current approval.

## 6. Recommended alternative and exact post-approval Preview command

Select an already initialised, dedicated project owned by `roomas-projects`.
Verify at least one deployment record remains, including errored/cancelled records;
a project from which all records were deleted is unsuitable. Do not repurpose an
active portfolio/application or alter its Production configuration implicitly.
Keep the current project/secrets intact until the replacement target is approved.

Before deploying to a replacement, verify its exact project ID/owner/Hobby plan,
existing workload, protection, aliases, Git settings, runtime and Preview-only
variable names. Securely provision only approved Preview values there, retain
mock transport guards, dummy provider key, Redis namespace `interviewiq-mocked-preview`,
Frankfurt and backend-only dependencies. Do not print secrets or use --env/--token
arguments for secret values. Review the same artifact manifest before upload.

Draft only; **not executed**. Replace the placeholder only after approval of the
specific previously initialised project. Run from the repository root:

```powershell
$approvedProject = '<approved-initialised-project-id>'
npx.cmd --yes --cache .npm-cache vercel@65.17.0 project inspect $approvedProject `
  --scope roomas-projects --format json --non-interactive
npx.cmd --yes --cache .npm-cache vercel@65.17.0 deploy .pytest_cache/phase3b-mocked-preview `
  --project $approvedProject --scope roomas-projects --environment preview `
  --regions fra1 --meta sourceCommit=bf445983c4d5e192dc86bb74b4436c962c1ddb7b `
  --meta sourceBranch=feat/streamlit-vercel-backend --meta mockOnly=true `
  --yes --non-interactive --no-wait --json
```

Expected: a Preview deployment, `target=null` in REST details, runtime
`VERCEL_ENV=preview`, Preview-scoped variables and protected URLs. Source metadata
records provenance; it does not select the target or make this byte-identical to
the published commit. Where branch-specific variables are used on a GitHub-linked
target, also supply the documented githubDeployment/githubCommitRef metadata for
the same repository/branch; generic sourceBranch metadata is not a substitute.
No promote, Production flag, custom domain assignment or paid option is proposed.
If the CLI reports first_deployment_production again, stop without retrying as Production.

After separate deployment approval, inspect environment classification before test
requests, verify unauthenticated denial on every assigned URL, then test health,
backend authentication, real Redis quotas, mocked workflows and deadlines using
header-only authorised protection bypass. Do not infer any hosted success now.

## Decision for approval

Recommended: approve a named, unused, previously initialised personal project for
protected Preview verification. If none exists, keep the current project idle and
seek Vercel confirmation of an explicit exception, or separately reconsider a
fully protected inert Production bootstrap. That last option would change the
current no-Production constraint and requires express new approval.

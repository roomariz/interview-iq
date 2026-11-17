# Additional dependency advisories found during remediation

Reviewed on 17 November 2026. The original five-package inventory is retained
in [the original advisory inventory](dependency-advisory-inventory.md).

The full development manifest exposed fpdf2 and pytest findings. An audit of
the actual installed environment then exposed stale transitive/local packages
that fresh manifest resolution had already replaced. All IDs are retained here.

| Package | Observed installed/resolved version | Advisory identifier | CVE/GHSA aliases | Reported fixed versions |
| --- | --- | --- | --- | --- |
| fpdf2 | 2.7.8 | [CVE-2026-114609](https://github.com/advisories/GHSA-rw7v-4hrq-x6r9) | GHSA-rw7v-4hrq-x6r9 | 2.8.8 |
| fpdf2 | 2.7.8 | [CVE-2026-114610](https://github.com/advisories/GHSA-wqw6-wpr3-45rh) | GHSA-wqw6-wpr3-45rh | 2.8.8 |
| pytest | 8.4.2 | [PYSEC-2026-1845](https://github.com/advisories/GHSA-6w46-j5rx-g56g) | GHSA-6w46-j5rx-g56g, CVE-2025-71176 | 9.0.3 |
| anyio | 4.13.0 | [PYSEC-2026-4024](https://github.com/advisories/GHSA-5p39-cfhj-2xmp) | CVE-2026-64847, GHSA-5p39-cfhj-2xmp | 4.14.2 |
| anyio | 4.13.0 | [PYSEC-2026-4025](https://github.com/advisories/GHSA-82r6-8w77-94w6) | GHSA-82r6-8w77-94w6, CVE-2026-63374 | 4.14.2 |
| certifi | 2026.4.22 | [PYSEC-2026-4320](https://github.com/advisories/GHSA-6q48-6c7w-9gw2) | GHSA-6q48-6c7w-9gw2 | 2026.10.18 |
| gitpython | 3.1.47 | [CVE-2026-110855](https://github.com/advisories/GHSA-fx3j-rwgx-fr94) | GHSA-fx3j-rwgx-fr94 | 3.2.0 |
| gitpython | 3.1.47 | [CVE-2026-110856](https://github.com/advisories/GHSA-m64x-33q8-m5h7) | GHSA-m64x-33q8-m5h7 | 3.2.0 |
| gitpython | 3.1.47 | [CVE-2026-110857](https://github.com/advisories/GHSA-w8jc-g24h-crhw) | GHSA-w8jc-g24h-crhw | 3.2.0 |
| gitpython | 3.1.47 | [CVE-2026-110858](https://github.com/advisories/GHSA-f9j4-qggq-h239) | GHSA-f9j4-qggq-h239 | 3.2.0 |
| gitpython | 3.1.47 | [CVE-2026-110859](https://github.com/advisories/GHSA-23mf-xhv8-69c2) | GHSA-23mf-xhv8-69c2 | 3.2.0 |
| gitpython | 3.1.47 | [CVE-2026-114145](https://github.com/advisories/GHSA-83vg-56qc-22m7) | GHSA-83vg-56qc-22m7 | 3.2.1 |
| gitpython | 3.1.47 | [PYSEC-2026-2162](https://github.com/advisories/GHSA-7545-fcxq-7j24) | GHSA-7545-fcxq-7j24, CVE-2026-44243 | 3.1.48 |
| gitpython | 3.1.47 | [PYSEC-2026-2163](https://github.com/advisories/GHSA-v87r-6q3f-2j67) | CVE-2026-44244, GHSA-v87r-6q3f-2j67 | 3.1.49 |
| gitpython | 3.1.47 | [PYSEC-2026-3783](https://github.com/advisories/GHSA-jm78-9fvv-mhgr) | CVE-2026-76221, GHSA-jm78-9fvv-mhgr | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3784](https://github.com/advisories/GHSA-hmq2-w58f-27jc) | CVE-2026-76222, GHSA-hmq2-w58f-27jc | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3785](https://github.com/advisories/GHSA-7833-fr7j-v32q) | CVE-2026-78675, GHSA-7833-fr7j-v32q | 3.1.59 |
| gitpython | 3.1.47 | [PYSEC-2026-3786](https://github.com/advisories/GHSA-284h-m62q-gf8w) | CVE-2026-78676, GHSA-284h-m62q-gf8w | 3.1.59 |
| gitpython | 3.1.47 | [PYSEC-2026-3787](https://github.com/advisories/GHSA-8mcc-hrx5-hvxc) | GHSA-8mcc-hrx5-hvxc, CVE-2026-78677 | 3.1.59 |
| gitpython | 3.1.47 | [PYSEC-2026-3788](https://github.com/advisories/GHSA-5xxx-qhh7-9287) | CVE-2026-78678, GHSA-5xxx-qhh7-9287 | 3.1.59 |
| gitpython | 3.1.47 | [PYSEC-2026-3836](https://github.com/advisories/GHSA-2f96-g7mh-g2hx) | GHSA-2f96-g7mh-g2hx, CVE-2026-67325 | 3.1.51 |
| gitpython | 3.1.47 | [PYSEC-2026-3837](https://github.com/advisories/GHSA-3wxw-xv34-2frg) | GHSA-3wxw-xv34-2frg, CVE-2026-78679 | 3.1.59 |
| gitpython | 3.1.47 | [PYSEC-2026-3838](https://github.com/advisories/GHSA-4gmw-gg2m-w46p) | GHSA-4gmw-gg2m-w46p, CVE-2026-76219 | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3839](https://github.com/advisories/GHSA-956x-8gvw-wg5v) | GHSA-956x-8gvw-wg5v, CVE-2026-67323 | 3.1.51 |
| gitpython | 3.1.47 | [PYSEC-2026-3840](https://github.com/advisories/GHSA-9rj7-rf2p-w77r) | GHSA-9rj7-rf2p-w77r, CVE-2026-76218 | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3841](https://github.com/advisories/GHSA-hh9p-6wh2-4mfc) | CVE-2026-76217, GHSA-hh9p-6wh2-4mfc | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3843](https://github.com/advisories/GHSA-wvpp-8hx9-p66j) | GHSA-wvpp-8hx9-p66j, CVE-2026-76220 | 3.1.58 |
| gitpython | 3.1.47 | [PYSEC-2026-3948](https://github.com/advisories/GHSA-539m-9xh6-q6rr) | GHSA-539m-9xh6-q6rr, CVE-2026-73619 | 3.1.57 |
| gitpython | 3.1.47 | [PYSEC-2026-3949](https://github.com/advisories/GHSA-3f7w-8rr8-f37f) | CVE-2026-73620, GHSA-3f7w-8rr8-f37f | 3.1.57 |
| gitpython | 3.1.47 | [PYSEC-2026-3950](https://github.com/advisories/GHSA-p538-c434-8v24) | GHSA-p538-c434-8v24, CVE-2026-73621 | 3.1.56 |
| gitpython | 3.1.47 | [PYSEC-2026-3951](https://github.com/advisories/GHSA-94p4-4cq8-9g67) | CVE-2026-73622, GHSA-94p4-4cq8-9g67 | 3.1.55 |
| gitpython | 3.1.47 | [PYSEC-2026-3952](https://github.com/advisories/GHSA-6p8h-3wgx-97gf) | GHSA-6p8h-3wgx-97gf, CVE-2026-73623 | 3.1.54 |
| gitpython | 3.1.47 | [PYSEC-2026-3953](https://github.com/advisories/GHSA-r9mr-m37c-5fr3) | CVE-2026-73625, GHSA-r9mr-m37c-5fr3 | 3.1.54 |
| gitpython | 3.1.47 | [PYSEC-2026-3980](https://github.com/advisories/GHSA-mv93-w799-cj2w) | GHSA-mv93-w799-cj2w, CVE-2026-67326 | 3.1.50 |
| gitpython | 3.1.47 | [PYSEC-2026-3981](https://github.com/advisories/GHSA-3rp5-jjmw-4wv2) | GHSA-3rp5-jjmw-4wv2, CVE-2026-69097 | 3.1.53 |
| gitpython | 3.1.47 | [PYSEC-2026-3982](https://github.com/advisories/GHSA-239g-whfq-7xj9) | CVE-2026-87817, GHSA-239g-whfq-7xj9 | 3.1.60 |
| gitpython | 3.1.47 | [PYSEC-2026-3984](https://github.com/advisories/GHSA-g5vv-9gxw-82hx) | CVE-2026-87819, GHSA-g5vv-9gxw-82hx | 3.1.60 |
| gitpython | 3.1.47 | [PYSEC-2026-3995](https://github.com/advisories/GHSA-fjr4-x663-mwxc) | CVE-2026-73624, GHSA-fjr4-x663-mwxc | 3.1.54 |
| idna | 3.13 | [PYSEC-2026-215](https://github.com/advisories/GHSA-65pc-fj4g-8rjx) | GHSA-65pc-fj4g-8rjx, CVE-2026-45409 | 3.15 |
| pip | 24.2 | [PYSEC-2026-1795](https://github.com/advisories/GHSA-4xh5-x5gv-qwph) | CVE-2025-8869, GHSA-4xh5-x5gv-qwph | 25.3 |
| pip | 24.2 | [PYSEC-2026-1796](https://github.com/advisories/GHSA-6vgw-5pg2-w6jp) | GHSA-6vgw-5pg2-w6jp, CVE-2026-1703 | 26.0 |
| pip | 24.2 | [PYSEC-2026-196](https://github.com/advisories/GHSA-wf93-45jw-7689) | CVE-2026-8643, GHSA-wf93-45jw-7689 | 26.1.2 |
| pip | 24.2 | [PYSEC-2026-2875](https://github.com/advisories/GHSA-58qw-9mgm-455v) | GHSA-58qw-9mgm-455v, CVE-2026-3219 | 26.1 |
| pip | 24.2 | [PYSEC-2026-2876](https://github.com/advisories/GHSA-jp4c-xjxw-mgf9) | GHSA-jp4c-xjxw-mgf9, CVE-2026-6357 | 26.1 |
| pip | 24.2 | [PYSEC-2026-3721](https://github.com/advisories/GHSA-qwm4-qh6w-59xr) | CVE-2026-13346, GHSA-qwm4-qh6w-59xr | 26.2.0 |
| tornado | 6.5.5 | [CVE-2026-115927](https://github.com/advisories/GHSA-r4j5-9xpp-3985) | GHSA-r4j5-9xpp-3985 | 6.6 |
| tornado | 6.5.5 | [CVE-2026-116577](https://github.com/advisories/GHSA-pcg2-g6cj-q92c) | GHSA-pcg2-g6cj-q92c | 6.6 |
| tornado | 6.5.5 | [CVE-2026-116578](https://github.com/advisories/GHSA-pw9p-v7r6-gx4p) | GHSA-pw9p-v7r6-gx4p | 6.6 |
| tornado | 6.5.5 | [CVE-2026-126347](https://github.com/advisories/GHSA-5cjw-f85j-cv6r) | GHSA-5cjw-f85j-cv6r | 6.6.1 |
| tornado | 6.5.5 | [GHSA-3hv7-mjh2-fv65](https://github.com/advisories/GHSA-3hv7-mjh2-fv65) | — | 6.5.9 |
| tornado | 6.5.5 | [GHSA-8423-8fgw-73vq](https://github.com/advisories/GHSA-8423-8fgw-73vq) | — | 6.5.8 |
| tornado | 6.5.5 | [GHSA-c2m8-h5v5-343r](https://github.com/advisories/GHSA-c2m8-h5v5-343r) | — | 6.5.9 |
| tornado | 6.5.5 | [GHSA-chx6-46f5-w4vp](https://github.com/advisories/GHSA-chx6-46f5-w4vp) | — | 6.5.9 |
| tornado | 6.5.5 | [GHSA-pw6j-qg29-8w7f](https://github.com/advisories/GHSA-pw6j-qg29-8w7f) | — | 6.5.7 |
| tornado | 6.5.5 | [GHSA-wwv5-g3v4-889x](https://github.com/advisories/GHSA-wwv5-g3v4-889x) | — | 6.5.8 |
| tornado | 6.5.5 | [PYSEC-2026-3387](https://github.com/advisories/GHSA-3x9g-8vmp-wqvf) | CVE-2026-49853, GHSA-3x9g-8vmp-wqvf | 6.5.6 |
| tornado | 6.5.5 | [PYSEC-2026-3388](https://github.com/advisories/GHSA-cx3h-4qpv-8hc9) | GHSA-cx3h-4qpv-8hc9, CVE-2026-49854 | 6.5.6 |
| tornado | 6.5.5 | [PYSEC-2026-3389](https://github.com/advisories/GHSA-mgf9-4vpg-hj56) | GHSA-mgf9-4vpg-hj56, CVE-2026-49855 | 6.5.6 |
| tornado | 6.5.5 | [PYSEC-2026-3928](https://github.com/advisories/GHSA-mpf4-983q-p7j4) | GHSA-mpf4-983q-p7j4, CVE-2026-82397 | 6.5.8 |
| urllib3 | 2.6.3 | [PYSEC-2026-141](https://github.com/advisories/GHSA-qccp-gfcp-xxvc) | GHSA-qccp-gfcp-xxvc, CVE-2026-44431 | 2.7.0 |
| urllib3 | 2.6.3 | [PYSEC-2026-142](https://github.com/advisories/GHSA-mf9v-mfxr-j63j) | GHSA-mf9v-mfxr-j63j, CVE-2026-44432 | 2.7.0 |
| urllib3 | 2.6.3 | [PYSEC-2026-4175](https://github.com/advisories/GHSA-8988-9cw3-xx77) | CVE-2026-97687, GHSA-8988-9cw3-xx77 | 2.8.0 |
| urllib3 | 2.6.3 | [PYSEC-2026-4176](https://github.com/advisories/GHSA-gh4c-6fx4-qh6g) | GHSA-gh4c-6fx4-qh6g, CVE-2026-97688 | 2.8.0 |
| urllib3 | 2.6.3 | [PYSEC-2026-4177](https://github.com/advisories/GHSA-vxq7-64xx-v4gw) | GHSA-vxq7-64xx-v4gw, CVE-2026-97689 | 2.8.0 |

## Deployment relevance

- anyio, certifi, idna and urllib3 are HTTP/TLS transitives used by runtime clients.
  They are now explicitly pinned in both deployment manifests and local requirements.
- fpdf2 belongs to the legacy local report helper; neither deployment requires it.
- pytest and pip are local test/install tools, excluded from the deployment manifests.
- GitPython and Tornado were left in the existing environment by older Streamlit.
  They are absent from the upgraded manifest resolutions and were patched locally;
  they were not added as new application dependencies.

These are version-based findings, not a claim that every vulnerable API was used.
See [the security review](dependency-security-review.md) for remediation and tests.

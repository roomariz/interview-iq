# Dependency advisory identifiers before remediation

Recorded from the 16 November 2026 merge audit; reviewed on 17 November 2026.
The original report had 100 entries and 71 distinct package/advisory-ID pairs.
Aliases and duplicate upstream records may refer to the same underlying issue.
This inventory preserves the original findings; remediation results are separate.

Originally installed: python-dotenv 1.0.1, requests 2.32.3, Streamlit 1.40.0,
Pillow 11.3.0 and Starlette 0.41.3. Installed FastAPI was 0.115.6.

## Identifiers, aliases and upstream patched versions

| Package | Advisory identifier | CVE / GHSA aliases | Reported fixed versions |
| --- | --- | --- | --- |
| python-dotenv | [PYSEC-2026-2270](https://github.com/advisories/GHSA-mf9w-mj56-hr94) | GHSA-mf9w-mj56-hr94, CVE-2026-28684 | 1.2.2 |
| requests | [PYSEC-2026-1872](https://github.com/advisories/GHSA-9hjg-9r4m-mvj7) | GHSA-9hjg-9r4m-mvj7, CVE-2024-47081 | 2.32.4 |
| requests | [PYSEC-2026-2275](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2) | CVE-2026-25645, GHSA-gc5v-m9x4-r6x2 | 2.33.0 |
| streamlit | [PYSEC-2026-212](https://github.com/advisories/GHSA-vqwp-45wm-r9r5) | GHSA-vqwp-45wm-r9r5, CVE-2026-10804 | 1.53.1 |
| streamlit | [PYSEC-2026-2285](https://github.com/advisories/GHSA-7p48-42j8-8846) | CVE-2026-33682, GHSA-7p48-42j8-8846 | 1.54.0 |
| pillow | [CVE-2026-112390](https://github.com/advisories/GHSA-22hg-r758-rrw9) | GHSA-22hg-r758-rrw9 | 13.0.0 |
| pillow | [CVE-2026-112391](https://github.com/advisories/GHSA-254f-3936-288h) | GHSA-254f-3936-288h | 13.0.0 |
| pillow | [CVE-2026-112393](https://github.com/advisories/GHSA-332p-7hrc-92wf) | GHSA-332p-7hrc-92wf | 13.0.0 |
| pillow | [CVE-2026-112395](https://github.com/advisories/GHSA-462x-pgg6-55fp) | GHSA-462x-pgg6-55fp | 13.0.0 |
| pillow | [CVE-2026-112399](https://github.com/advisories/GHSA-5xm2-6676-qcp9) | GHSA-5xm2-6676-qcp9 | 13.0.0 |
| pillow | [CVE-2026-112400](https://github.com/advisories/GHSA-65qm-jvmh-6pqg) | GHSA-65qm-jvmh-6pqg | 13.0.0 |
| pillow | [CVE-2026-112401](https://github.com/advisories/GHSA-74r2-7ff9-mjj2) | GHSA-74r2-7ff9-mjj2 | 13.0.0 |
| pillow | [CVE-2026-112404](https://github.com/advisories/GHSA-c6hw-5grf-ff96) | GHSA-c6hw-5grf-ff96 | 13.0.0 |
| pillow | [CVE-2026-112406](https://github.com/advisories/GHSA-f2g6-542v-9j58) | GHSA-f2g6-542v-9j58 | 13.0.0 |
| pillow | [CVE-2026-112891](https://github.com/advisories/GHSA-fc9g-5qg7-mf45) | GHSA-fc9g-5qg7-mf45 | 13.0.0 |
| pillow | [CVE-2026-112892](https://github.com/advisories/GHSA-gg2r-wvfm-q9rx) | GHSA-gg2r-wvfm-q9rx | 13.0.0 |
| pillow | [CVE-2026-112893](https://github.com/advisories/GHSA-j4m9-6w36-pw47) | GHSA-j4m9-6w36-pw47 | 13.0.0 |
| pillow | [CVE-2026-112894](https://github.com/advisories/GHSA-jg86-v3jv-hrpm) | GHSA-jg86-v3jv-hrpm | 13.0.0 |
| pillow | [CVE-2026-112895](https://github.com/advisories/GHSA-p4wg-p73j-c528) | GHSA-p4wg-p73j-c528 | 13.0.0 |
| pillow | [CVE-2026-112897](https://github.com/advisories/GHSA-q45j-58j2-45rg) | GHSA-q45j-58j2-45rg | 13.0.0 |
| pillow | [CVE-2026-112899](https://github.com/advisories/GHSA-vx6w-vv9f-6gvg) | GHSA-vx6w-vv9f-6gvg | 13.0.0 |
| pillow | [CVE-2026-112900](https://github.com/advisories/GHSA-w889-685w-c8fh) | GHSA-w889-685w-c8fh | 13.0.0 |
| pillow | [CVE-2026-128066](https://github.com/advisories/GHSA-wqgw-9xfh-qf2g) | GHSA-wqgw-9xfh-qf2g | 13.0.0 |
| pillow | [CVE-2026-128067](https://github.com/advisories/GHSA-xcvg-w56q-r89m) | GHSA-xcvg-w56q-r89m | 13.0.0 |
| pillow | [CVE-2026-96638](https://github.com/advisories/GHSA-24rc-8hj2-v98c) | GHSA-24rc-8hj2-v98c | 13.0.0 |
| pillow | [CVE-2026-96640](https://github.com/advisories/GHSA-mrfp-p49p-3hf2) | GHSA-mrfp-p49p-3hf2 | 13.0.0 |
| pillow | [CVE-2026-96778](https://github.com/advisories/GHSA-g7cr-3p24-7wf7) | GHSA-g7cr-3p24-7wf7 | 13.0.0 |
| pillow | [GHSA-78g4-xqwv-q3g8](https://github.com/advisories/GHSA-78g4-xqwv-q3g8) | — | 13.0.0 |
| pillow | [PYSEC-2026-165](https://github.com/advisories/GHSA-wjx4-4jcj-g98j) | GHSA-wjx4-4jcj-g98j, CVE-2026-42308 | 12.2.0 |
| pillow | [PYSEC-2026-2249](https://github.com/advisories/GHSA-cfh3-3jmp-rvhc) | GHSA-cfh3-3jmp-rvhc, CVE-2026-25990 | 12.1.1 |
| pillow | [PYSEC-2026-2250](https://github.com/advisories/GHSA-whj4-6x5x-4v2j) | GHSA-whj4-6x5x-4v2j, CVE-2026-40192 | 12.2.0 |
| pillow | [PYSEC-2026-2251](https://github.com/advisories/GHSA-5xmw-vc9v-4wf2) | CVE-2026-42309, GHSA-5xmw-vc9v-4wf2 | 12.2.0 |
| pillow | [PYSEC-2026-2252](https://github.com/advisories/GHSA-pwv6-vv43-88gr) | CVE-2026-42311, GHSA-pwv6-vv43-88gr | 12.2.0 |
| pillow | [PYSEC-2026-2253](https://github.com/advisories/GHSA-8v84-f9pq-wr9x) | CVE-2026-54059, BIT-pillow-2026-54059, GHSA-8v84-f9pq-wr9x | 12.3.0 |
| pillow | [PYSEC-2026-2254](https://github.com/advisories/GHSA-5x94-69rx-g8h2) | CVE-2026-54060, BIT-pillow-2026-54060, GHSA-5x94-69rx-g8h2 | 12.3.0 |
| pillow | [PYSEC-2026-2255](https://github.com/advisories/GHSA-45hq-cxwh-f6vc) | CVE-2026-55379, BIT-pillow-2026-55379, GHSA-45hq-cxwh-f6vc | 12.3.0 |
| pillow | [PYSEC-2026-2256](https://github.com/advisories/GHSA-phj9-mv4w-65pm) | BIT-pillow-2026-55380, CVE-2026-55380, GHSA-phj9-mv4w-65pm | 12.3.0 |
| pillow | [PYSEC-2026-2257](https://github.com/advisories/GHSA-4x4j-2g7c-83w6) | GHSA-4x4j-2g7c-83w6, CVE-2026-55798 | 12.3.0 |
| pillow | [PYSEC-2026-2874](https://github.com/advisories/GHSA-r73j-pqj5-w3x7) | CVE-2026-42310, GHSA-r73j-pqj5-w3x7 | 12.2.0 |
| pillow | [PYSEC-2026-3451](https://github.com/advisories/GHSA-6r8x-57c9-28j4) | BIT-pillow-2026-59199, GHSA-6r8x-57c9-28j4, CVE-2026-59199 | 12.3.0 |
| pillow | [PYSEC-2026-3453](https://github.com/advisories/GHSA-9hw9-ch79-4vh6) | GHSA-9hw9-ch79-4vh6, CVE-2026-59205, BIT-pillow-2026-59205 | 12.3.0 |
| pillow | [PYSEC-2026-3454](https://github.com/advisories/GHSA-xj96-63gp-2gmr) | GHSA-xj96-63gp-2gmr, CVE-2026-59197 | 12.3.0 |
| pillow | [PYSEC-2026-3493](https://github.com/advisories/GHSA-62p4-gmf7-7g93) | CVE-2026-54058, GHSA-62p4-gmf7-7g93 | 12.3.0 |
| pillow | [PYSEC-2026-3494](https://github.com/advisories/GHSA-fj7v-r99m-22gq) | CVE-2026-59198, GHSA-fj7v-r99m-22gq | 12.3.0 |
| pillow | [PYSEC-2026-3495](https://github.com/advisories/GHSA-jjj6-mw9f-p565) | CVE-2026-59200, GHSA-jjj6-mw9f-p565 | 12.3.0 |
| pillow | [PYSEC-2026-3496](https://github.com/advisories/GHSA-vjc4-5qp5-m44j) | CVE-2026-59204, GHSA-vjc4-5qp5-m44j | 12.3.0 |
| pillow | [PYSEC-2026-4326](https://github.com/advisories/GHSA-27h8-gf7j-v5hc) | CVE-2026-112392, GHSA-27h8-gf7j-v5hc | 13.0.0 |
| pillow | [PYSEC-2026-4327](https://github.com/advisories/GHSA-4558-3h8r-v8xp) | CVE-2026-112394, GHSA-4558-3h8r-v8xp | 13.0.0 |
| pillow | [PYSEC-2026-4328](https://github.com/advisories/GHSA-4rr5-89j8-mwwm) | CVE-2026-112396, GHSA-4rr5-89j8-mwwm | 13.0.0 |
| pillow | [PYSEC-2026-4329](https://github.com/advisories/GHSA-58r4-6rv3-gfh8) | CVE-2026-112397, GHSA-58r4-6rv3-gfh8 | 13.0.0 |
| pillow | [PYSEC-2026-4330](https://github.com/advisories/GHSA-5x8w-8jj5-q52h) | GHSA-5x8w-8jj5-q52h, CVE-2026-112398 | 13.0.0 |
| pillow | [PYSEC-2026-4331](https://github.com/advisories/GHSA-7mwm-ghpf-9vrm) | GHSA-7mwm-ghpf-9vrm, CVE-2026-112402 | 13.0.0 |
| pillow | [PYSEC-2026-4332](https://github.com/advisories/GHSA-8g5g-8vmr-9782) | GHSA-8g5g-8vmr-9782, CVE-2026-112403 | 13.0.0 |
| pillow | [PYSEC-2026-4334](https://github.com/advisories/GHSA-pchr-8j38-3x4p) | CVE-2026-112896, GHSA-pchr-8j38-3x4p | 13.0.0 |
| pillow | [PYSEC-2026-4335](https://github.com/advisories/GHSA-xgh8-jp6q-p5x8) | CVE-2026-112901, GHSA-xgh8-jp6q-p5x8 | 13.0.0 |
| pillow | [PYSEC-2026-4336](https://github.com/advisories/GHSA-654x-cwwv-5j9c) | CVE-2026-114501, GHSA-654x-cwwv-5j9c | 13.0.0 |
| pillow | [PYSEC-2026-4337](https://github.com/advisories/GHSA-p8hx-v2p6-rp84) | CVE-2026-96636, GHSA-p8hx-v2p6-rp84 | 13.0.0 |
| pillow | [PYSEC-2026-4338](https://github.com/advisories/GHSA-g842-9rc4-69pw) | CVE-2026-96637, GHSA-g842-9rc4-69pw | 13.0.0 |
| pillow | [PYSEC-2026-4339](https://github.com/advisories/GHSA-v9pv-5gc8-w2m6) | CVE-2026-96639, GHSA-v9pv-5gc8-w2m6 | 13.0.0 |
| pillow | [PYSEC-2026-4340](https://github.com/advisories/GHSA-4rm8-3hmm-39fg) | CVE-2026-96641, GHSA-4rm8-3hmm-39fg | 13.0.0 |
| pillow | [PYSEC-2026-4341](https://github.com/advisories/GHSA-3j72-p6qg-6xp7) | CVE-2026-96642, GHSA-3j72-p6qg-6xp7 | 13.0.0 |
| pillow | [PYSEC-2026-4342](https://github.com/advisories/GHSA-g4qv-2jxx-769h) | GHSA-g4qv-2jxx-769h, CVE-2026-96643 | 13.0.0 |
| pillow | [PYSEC-2026-4343](https://github.com/advisories/GHSA-9v9v-9qvf-h2hj) | GHSA-9v9v-9qvf-h2hj, CVE-2026-96644 | 13.0.0 |
| pillow | [PYSEC-2026-4363](https://github.com/advisories/GHSA-xvh5-g6gv-559v) | CVE-2026-112902, GHSA-xvh5-g6gv-559v | 13.0.0 |
| starlette | [PYSEC-2026-161](https://github.com/advisories/GHSA-86qp-5c8j-p5mr) | X41-2026-002, GHSA-86qp-5c8j-p5mr, CVE-2026-48710 | 1.0.1 |
| starlette | [PYSEC-2026-1941](https://github.com/advisories/GHSA-2c2j-9gv5-cj73) | GHSA-2c2j-9gv5-cj73, CVE-2025-54121 | 0.47.2 |
| starlette | [PYSEC-2026-1942](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8) | GHSA-7f5h-v6xp-fcq8, CVE-2025-62727 | 0.49.1 |
| starlette | [PYSEC-2026-2280](https://github.com/advisories/GHSA-x746-7m8f-x49c) | GHSA-x746-7m8f-x49c, CVE-2026-48817 | 1.1.0 |
| starlette | [PYSEC-2026-2281](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r) | CVE-2026-48818, GHSA-wqp7-x3pw-xc5r | 1.1.0 |
| starlette | [PYSEC-2026-248](https://github.com/advisories/GHSA-jp82-jpqv-5vv3) | CVE-2026-54282, GHSA-jp82-jpqv-5vv3 | 1.3.0 |
| starlette | [PYSEC-2026-249](https://github.com/advisories/GHSA-82w8-qh3p-5jfq) | GHSA-82w8-qh3p-5jfq, CVE-2026-54283 | 1.3.1 |

## Scope

python-dotenv, requests and Starlette were in the deployed backend manifest.
Streamlit and Pillow were frontend dependencies, also present in local development.
None of the original five was exclusively a test/development dependency.
The upgraded Streamlit also depends on Starlette; its patched pin now covers
both runtime manifests. The deployed backend still excludes Streamlit and Pillow.

Fixed versions above are upstream advisory data, not independent proof that an
entire environment is secure. See [remediation review](dependency-security-review.md)
for selected compatible versions, exposure, fresh audits and regression results.

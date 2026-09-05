# Peano preview delivery — verified 2026-09-05

This is the preserved preview-phase receipt. The owner subsequently approved
and completed a separate [production promotion](PEANO_PHP_PRODUCTION_2026-09-05.md);
the production-unchanged statements below describe this earlier phase.

The read-only PHP delivery adapter is deployed and verified on
[Peano preview](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/).
The existing full HTTPS release gate passes without modifications.
Production, the proof website, the independent Lean companion and mathematical
admissions were not changed by this work.

## Frozen identities and authorization

The owner approved implementation and testing of the Peano-only adapter on
preview, preserving all release checks. This is not production authorization.
Source was clean and pushed before routing activation:

- Initial implementation: `b949a14722b1351b98ec8616650e6e795a8d05b2`.
- Corrected, deployed source: `a420b8dd8c3dc2bf8f012a3b10d4b7f3d24f6a67`.
- Branch: `fix/proof-explorer-layout-20260904` in `nasqret/vietnam2026`.
- Private stage receipt SHA-256: `36cfab37e22f8fc892b0c81d97d2c99bc8953acef0967d8c07e9860291a89ac3`.
- Unchanged app `a-4de50afd4366`, vendor `v-85fb3352e49c`, build `2026-09-05a`.

The separate `_deploy/peano-lab-php` assembly contains 1,878 files and 622
deterministic gzip representations. All 630 original public files are
byte-identical; only delivery code, routing and private transport data were
added/changed. The earlier assembly is retained as
`_deploy/peano-lab-php-attempt1`, and the original static stage remains intact.
This is a transport repair, not reuse of an application ID for different bytes.

## Initial failure and recovery

The first activation returned HTTP 500. Its unchanged release gate stopped the
deployment, and the operator procedure automatically restored the original
preview `.htaccess`. The restored routing and index hashes both matched.

The cause was an interpreter mismatch: SSH runs PHP `7.4.3-4ubuntu2.29`, while
public FPM runs `7.0.33-0+deb9u24`. The first implementation used nullable/void
types and short destructuring unavailable in PHP 7.0. Those syntax features
were replaced without changing the request policy, file checks or release gate.
A regression guard covers the observed syntax floor. Before routing was retried,
a direct web-runtime diagnostic returned the expected 404 with `fatal: null`.
The temporary diagnostic was then moved out of public hosting into the private
QA directory; its retained copy and public absence were verified.

The corrected activation verified all 1,877 payload/handler files before
switching routing, ran the full HTTPS gate, then verified all 1,878 final files.
No previous application/vendor namespace was deleted. The original routing
backup remains available. Production's entrypoint and routing hashes are
unchanged.

## Validation results

- 162 Python regression tests passed in 56.00 seconds, with five pre-existing
  invalid-escape deprecation warnings; no test was skipped to obtain the pass.
- 98 portable PHP checks passed on WMI CLI under a 64 MiB memory limit;
  measured peak allocation was 2 MiB. This is a CLI measurement, not an FPM
  load-test or browser-memory claim.
- The original delivery verifier passed on real HTTPS/FPM. It checks every one
  of the 609 current application files, no-store HTML including 304, immutable
  responses including 304/206, negotiated compression and decoded WASM identity,
  gzip/q=0/identity handling, ZIP/WOFF2 exclusions and no-store missing-resource
  responses. Encoded WASM is **2,817,221 bytes**, below the unchanged 3,000,000
  byte bound.
- 134 additional HTTPS responses passed: 114 exact-body comparisons comprise
  the manifest, worker, driver and checker in each of 15 retained applications,
  plus all 18 vendor files at the canonical, historical and flat URL layouts.
  Remaining checks cover private/unlisted paths, the removed diagnostic,
  query non-authority, POST/OPTIONS rejection, conditional requests and errors.
- WMI's upstream `.htaccess` protection returns 403 without a cache header,
  outside the PHP adapter. The supplementary audit originally expected an
  adapter 404 there; it was corrected to test the observed protected boundary
  separately. No server protection or release-gate assertion was weakened.

The unchanged verifier's final output was:

```text
Verified https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next: build=2026-09-05a app=a-4de50afd4366 vendor=v-85fb3352e49c encoded_wasm=2817221 bytes
```

The [machine-readable observation receipt](../research/arithmetic-library/working/peano-php-delivery-v1/preview-deployment-v2.json)
pins the source, stage and local raw observation logs. The earlier
[preflight receipt](../research/arithmetic-library/working/peano-php-delivery-v1/preflight-observations-v1.json)
is preserved as a historical preflight result, not relabeled as a successful
first deployment.

## Remaining boundaries

Browser discovery returned no available browser, including the final retry.
No screenshots, measured cold/warm starts, checked-QED interaction, Stop/restart
test or browser-memory result is claimed. Connect the in-app Browser to run
those acceptance checks. Production requires its own authorization, retained
rollback, identical stage validation and full HTTPS/browser checks.

PHP 7.0 and 7.4 are [unsupported upstream](https://www.php.net/eol.php).
Distribution/vendor extended-security support was not audited. WMI should
confirm its support arrangements or upgrade the runtime independently; passing
delivery tests is not a security certification of the hosting stack.

The constructive-proof-explorer skill guided exact-byte/evidence preservation.
The Browser skill required a connected browser and therefore left interactive
QA explicitly pending. No GitHub Actions run or new independent Lean compilation
is claimed for this transport-only release. Other research worktrees are
unrelated and were not modified.

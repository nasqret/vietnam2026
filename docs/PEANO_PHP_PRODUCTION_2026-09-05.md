# Peano production promotion — verified 2026-09-05

[Production Peano Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/)
now serves build `2026-09-05a`, app `a-4de50afd4366`, using exactly the verified
preview assembly. The unchanged full HTTPS release gate passes. No PHP code,
browser code, proof artifact, kernel, library admission or release gate was
modified for this promotion.

## Authority and exact candidate

The owner explicitly requested and approved production changes after the
preview result and unavailable-browser limitation were reported. This
authorization is specific to this promotion, not automatic approval of later
releases or evidence that interactive browser acceptance has passed.

- Clean, pushed source at activation: `17eccf6b4158e5bfdbfa6b033d26640474c85574`.
- Branch: `fix/proof-explorer-layout-20260904`, repository `nasqret/vietnam2026`.
- Exact stage receipt SHA-256: `36cfab37e22f8fc892b0c81d97d2c99bc8953acef0967d8c07e9860291a89ac3`.
- Previous production: build `2026-08-26e`, app `a-a4f746a1cd35`.
- Promoted build/app/vendor: `2026-09-05a` / `a-4de50afd4366` / `v-85fb3352e49c`.

The [preview receipt](PEANO_PHP_DELIVERY_DEPLOYMENT_2026-09-05.md) retains the
implementation history, PHP-runtime correction and original validation.
The [production observation receipt](../research/arithmetic-library/working/peano-php-delivery-v1/production-deployment-v1.json)
pins this separate promotion and its raw operator observations.

## Safe transition and retention

The preflight authenticated all 2,146 existing production files and all five
retained application manifests. The checksum dry run showed 1,857 additions
and only two existing content replacements: `index.html` and `.htaccess`.
The vendor manifest and all existing immutable bytes matched. No remote
deletion was used, and the source remained frozen until verification completed.

Original HTML, routing and vendor-manifest bytes were backed up both locally
and in a new private, mode-0700 directory outside public hosting. Both copies
were hash-verified. Upload order was dependencies, handler, HTML pointer, then
routing. All pre-activation files were compared before switching the controls.
A direct request to the inactive handler returned its expected no-store 404.
After activation, every staged and retained file was compared again. The
rollback path was armed but not needed.

All 4,003 final files match the expected union of retained and promoted bytes.
This includes all 1,878 files of the exact preview stage. Of the 2,146 previous
files, 2,144 retain their original contents; the other two have verified backups.
The five retained application namespaces and the canonical/flat vendor layouts
were checked over actual HTTPS. Preview's entrypoint, routing, handler and stage
receipt hashes remain unchanged. The separate proof site was not deployed.

The 32 pre-versioning flat worker/Python files remain on disk. As in preview,
those unversioned application paths are outside the adapter's manifest-only
public route contract; this retention claim concerns their bytes, not public
routing. Current and retained versioned application paths are covered by the
delivery checks.

## Verification

- Fresh focused packaging/CI regression run: 54 tests passed.
- Portable PHP suite: 98 checks passed against the exact deployed handler.
- Before activation, the handler prepared all 2,685 authenticated application
  file responses across six versions, with no failures and 2 MiB peak CLI
  allocation under a 64 MiB limit. These are file-delivery checks, not theorem
  re-proofs, browser timing measurements or a new formal soundness claim.
- The unchanged production HTTPS gate verified all 609 current application
  files, no-store HTML on 200/304, immutable versioned responses on 200/304/206,
  compression negotiation, decoded WASM identity, q=0/gzip/identity behavior,
  ZIP/WOFF2 exclusions and no-store missing-resource responses.
- Encoded WASM: **2,817,221 bytes**, below the unchanged 3,000,000-byte bound.
- 62 supplementary live checks passed: 56 exact-body comparisons (four files
  in each of five retained apps and all 18 files in each of two vendor layouts),
  four private/unlisted-path denials and POST/OPTIONS rejection.

The original verifier reported:

```text
Verified https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab: build=2026-09-05a app=a-4de50afd4366 vendor=v-85fb3352e49c encoded_wasm=2817221 bytes
```

## Remaining acceptance and hosting concerns

The Browser skill found no connected browser. No screenshot, cold/warm-start
measurement, interactive QED or Stop/restart result is claimed. Those checks
remain pending even though the owner-approved production deployment and full
HTTP verification are complete. No new GitHub Actions or independent Lean
compilation is claimed for this unchanged-payload promotion.

The existing [PHP support concern](PEANO_PHP_DELIVERY.md#why-this-exists)
also remains: upstream PHP 7.0/7.4 support has ended, and WMI's extended-support
arrangements were not audited. No central hosting configuration, daemon,
credential, training job or proof authority was changed. The
constructive-proof-explorer skill guided evidence and presentation preservation;
unrelated worktrees and the independent Lean repository were untouched.

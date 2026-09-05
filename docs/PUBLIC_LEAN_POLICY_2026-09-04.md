# Public Lean controls hidden — 2026-09-04

The public proof site no longer creates the on-demand Lean build card.
This applies to all 8,264 selector-enabled graph/theorem pages across
68 proof families. Existing tabs need a reload to receive the changed script.

The user requested that this unreliable public feature be hidden or replaced
with Lean Live. The checked public release contains neither standalone `.lean`
exports nor authenticated static Lean Live links. The selected implementation
therefore hides the public controls without substituting an empty playground
or claiming that a theorem has been compiled by Lean Live.

## Exact scope

Only `assets/lean-selector.js` was replaced, with the 330-byte inactive
`deploy/proofs/lean-selector-disabled.js`. It creates no controls, performs
no DOM operations and makes no network requests. The 3,184-byte
`presentation/lean-policy-v1.json` was added as a non-admitting policy record.

Every HTML page, graph dataset, definition, proof artifact, historical release
manifest and original exact/defined reader asset remains byte-identical to
the previously verified layout stage. The canonical local Lean selector,
worker, gateway and private SSH/mailbox configuration were not changed.
No service was started, restarted or stopped; no new proof job was submitted.

The final publication target now creates or rechecks `_deploy/proofs-public-v1`
from the preserved `_deploy/proofs-layout-v1` tree. Future normal deployments
use this final tree. Deploying an earlier stage alone would restore the
public controls and must not be used as a routine deployment.

## Verification

- 129 relevant tests passed, including the local selector's interaction
  harness, the inactive public script's no-DOM/no-network execution, the
  existing layout regressions, staging safety and deployment contracts.
- Three legacy selector tests were corrected to distinguish non-admitting
  checkpoint file inventories from Alpha family manifests; no proof
  artifacts or admission criteria were changed.
- Complete staging and a separate fresh recheck passed: 13,551 output files,
  one changed input asset, one added policy manifest, zero changed HTML bytes.
- The two-file rsync dry run and upload completed with no unexpected changes
  or deletions, preserving existing directory timestamps and public permissions.
- All 13,551 deployed file hashes matched the checked final stage.
- All 80 public HTTPS content checks passed, covering every family and both
  reading editions, representative graphs/definitions, the reported
  Quadratic Reciprocity page, both presentation manifests and the new selector.

The public selector returns HTTP 200 with its new ETag and Last-Modified.
Its observed HEAD response did not include a Cache-Control header; no
hosting-header configuration was changed. Refresh existing pages to unload
the already-executed old selector. Verification used the JavaScript harness,
exact HTTP content checks and a full remote hash audit, not a browser screenshot.

## Delivery identities

Preserved layout manifest SHA-256:
`14238ef05845f5a97c130814b93e1b65619c88ce7ca9c59cd2e825b4b9efca3f`.

Public policy manifest SHA-256:
`ac463f91abecc4da1db5be466d7215adaa9002d0450f41f973977630bdd95aac`.

Inactive public selector SHA-256:
`480a985a70a3d539f74285c5cd5cb661e210e194edac3f297c09ce17a2756d5d`.

Preserved canonical local selector SHA-256:
`5759acfe73c5039aa8f0770429727d9d6d82d61265d1bf6731a79f2183651335`.

Local deployment observations are retained under `_deploy/` as
`public-lean-policy-preview-v1.json`, `public-lean-policy-upload-v1.json`,
`public-lean-policy-remote-after-v1.json` and `public-lean-policy-https-v1.json`.

## A future static Lean Live option

A direct theorem link should be published only after its complete standalone
source is generated, independently compiled and bound to an authenticated
share URL. Proofs requiring private companion imports or exceeding supported
source/link limits must retain honest availability labels. Such static exports
would not depend on the owner's machine or the faculty SSH tunnel being online.

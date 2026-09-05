# Proof explorer layout repair — 2026-09-04

Deployed to the faculty proof website: 9,900 HTML pages across all 68 families.
The reported Quadratic Reciprocity page, `PA00A7`, now serves the corrected
markup at its original URL, without requiring a cache-busting query.

## Cause and scope

The current-release notice was inserted as a direct child of the theorem
page's two-column grid. It occupied the first grid cell, placing the proof
in the narrow right-hand column and displacing its receipt sidebar.

The repair adds `style="grid-column: 1 / -1;"` to the actual direct-child
release-notice paragraph. The notice occupies one full-width row; the proof
and sidebar occupy their original columns below it. The existing mobile
single-column layout remains applicable. Each changed page gains exactly
29 bytes. No proof text, definitions, graph data, original CSS/JavaScript,
historical manifests or mathematical evidence is modified.

`scripts/proof_explorer_layout.py` performs a byte-preserving, idempotent
HTML transformation, rejecting ambiguous or conflicting notices. The
stager preserves the accepted v34 tree and verifies the complete new tree.
`make stage-proofs` and `make deploy-proofs` use this final presentation
layer, so a normal subsequent deployment retains the repair.

## Verification

- 46 focused regression and deployment-contract tests passed.
- The complete local stage contains 13,550 files, including one new
  presentation manifest; both staging and a fresh full recheck passed.
- Before upload, all 9,900 affected live pages and the original release
  manifest matched the preserved base (9,901 exact matches).
- The dry run and actual upload contained exactly 9,900 changed pages and
  the new presentation manifest, with no unexpected file changes or deletions.
- After upload, all 9,900 pages and both manifests matched their expected
  hashes (9,902 exact matches).
- 78 final public HTTPS checks returned HTTP 200 and exact expected bytes,
  sampling all 68 families, both reading editions, graph/index/definition
  pages, the reported URL with and without a query, and the new manifest.

Browser UI validation was unavailable because no in-app browser was connected.
No screenshot or interactive-browser verification is claimed.

## Exact delivery identity

Preserved base: `release-v34/manifest.json`, 2,212,991 bytes,
SHA-256 `7be4ebc968b7e60d79b387f292c8700053a1b48a7ca3598c85a64e27f5b6fa22`.

Presentation manifest: `presentation/layout-v1.json`, 2,651,605 bytes,
SHA-256 `14238ef05845f5a97c130814b93e1b65619c88ce7ca9c59cd2e825b4b9efca3f`.
It records every changed page's before/after hashes and the stager controls.

Reported page: `quadratic-reciprocity/explorer/defined/tag/PA00A7.html`,
32,516 bytes after repair,
SHA-256 `2e08c22bb8b365416728efc6411f1f09de07574914eaad39895beeb110885f79`.

Local observations are retained under `_deploy/`:

- `proof-layout-tests-v1.json`
- `proof-layout-rsync-preview-v2.json`
- `proof-layout-rsync-upload-v1.json`
- `proof-layout-remote-before-v1.json`
- `proof-layout-remote-after-v1.json`
- `proof-layout-manifest-permissions-v1.json`
- `proof-layout-https-v2.json`

The first read-only transfer preview exposed an incompatibility with
macOS openrsync's `--no-implied-dirs`; it changed no files. The successful
targeted transfer used `--files-from=-` and `--omit-dir-times`, preserving
existing directory attributes. The server's restrictive creation umask
initially made the new manifest private. Only that newly created directory
and file were corrected to modes 755 and 644, respectively; the final
HTTPS checks above were run after that correction.

This was a presentation-only deployment, not an Alpha/Stable promotion.
The Lean API and unrelated worktrees were not deployed or modified. The
preserved `_deploy/proofs-v34` tree provides the exact pre-repair rollback.

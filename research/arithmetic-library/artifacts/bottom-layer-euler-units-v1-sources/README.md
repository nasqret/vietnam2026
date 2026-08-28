# Superseded non-admitting Euler v1 authoring sources

These four files are byte-exact copies from the locally generated v1 proof
explorer, saved before its Euler chapter was deduplicated. They are historical
evidence only: do not import them into the active theorem inventory.

The three module hashes match the original 34-row checkpoint's literal source
pins. The RFC is its original authoring receipt. See `manifest.json` for every
file size and SHA-256; no current working mathematical source was copied here.

Two statements were already present in immutable Alpha v30:

- `euler_modulus_above_one_nonzero` duplicates
  `binary_modulus_nontrivial_nonzero` (reserved local tag `EU0003`).
- `euler_product_scale_shuffle` duplicates `mul_shuffle_four`
  (reserved local tag `EU001C`).

The active Euler checkpoint therefore has 32 distinct new theorems. All other
local Euler tags, including the endpoint `EU0022`, remain unchanged. The
[original v1 proof bundle](../bottom-layer-euler-units-proof-bundle-v1.json)
is retained separately, together with its historical audit. That bundle
remains ordinary checkable proof data; these sources are not a new admission
or a replacement for fresh original-HA and compiled-Lean verification.

Neither v1 nor its successor grants Alpha or Stable membership. Alpha v30
remains 3222 checked-use entries and Stable remains 432. Nothing in this
archive asserts that the v1 tests or authoring files are the active versions.

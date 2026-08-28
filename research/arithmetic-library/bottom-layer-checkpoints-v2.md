# Bottom-layer checkpoint: 170 new constructive theorems

2026-08-28. Local implementation on `proof/lower-foundations-v31-20260828`,
based on published commit `18ce79d3137616687183d17fcaed0a2c1383fecf`.
This is **not an Alpha edition or a deployment**. Alpha v30 remains at 3,222
checked-use entries and default Stable at 432; their artifacts are untouched.

## Completed mathematics

| Family | New theorems | Complete bundle nodes | Bundle edges | Exact scope |
| --- | ---: | ---: | ---: | --- |
| Euler units | 32 | 210 | 568 | Full G014 endpoint, with the actual existing totient graph and a constructed power witness |
| Prime fields | 87 | 228 | 611 | Actual operation tables, twenty field laws, a p-element bijection and characteristic p |
| Möbius values | 21 | 237 | 675 | Positive-domain totality/uniqueness, square cases and fresh-prime negation |
| Signed finite sums | 30 | 214 | 571 | Actual signed tables, representation-independent folds, constructed reindexing and permutation invariance |

Bundle counts include inherited theorem bodies and one packaging root; they
are not additional theorem counts. All eleven new modules are ordinary
first-order Heyting-arithmetic proof scripts over the unchanged kernel.

The final exhaustive AST audit checks every one of the 3,222 parent
statements, without filtering by source length. It found two initial Euler
duplicates, now replaced by direct reuse of
`binary_modulus_nontrivial_nonzero` and `mul_shuffle_four`. All 170 active
statements are pairwise distinct and are not exact parent clones. The
superseded 34-row Euler bundle and v1 audit remain valid historical proof
data, with their original source bytes preserved in
[the v1 source archive](artifacts/bottom-layer-euler-units-v1-sources/README.md).
They are not additional current theorem entries or Alpha admissions.

The Euler endpoint is

```text
forall a m t.
  (Lt(1,m) /\ (Unit(a,m) /\ Phi(m,t))) ->
  exists w. Pow(a,t,w) /\ ModEq(m,w,1).
```

`Unit(a,m)` means a genuinely witnessed inverse, not just a nonzero residue.
The broader coprime form includes modulus one and concludes congruence to
one, not the false assertion that one is its canonical remainder. The proof
constructs multiplication by a unit as a bounded permutation, connects an
actual weighted product with the independently defined totient count, and
cancels a proved coprime product.

Prime-field existence supplies ten real beta-code parameters for operations
and enumeration. Repeated addition of one is an actual history whose residue
invariant is proved by induction. The inverse table's `0 -> 0` convention
does not assert an inverse for zero. Full **G091 remains open**: arbitrary
positive extension degrees, irreducible polynomials and the complete
prime-power-field endpoint are not supplied by these prime-order results.

Möbius values use actual prime-square divisibility and the parity of a genuine
prime factor list. Signed codes are 0 for zero, 2 for positive one and 1 for
negative one. Signed sums use two actual natural-component beta streams and
canonical signed balance; different component representations need not be
equal. Full **G007 remains open**: its divisor masks, cancellation identity,
weighted finite Fubini/convolution and inversion endpoint still need proofs.

Detailed authoring contracts:
[Euler](euler-units-rfc-v1.md),
[prime fields](prime-field-arithmetic-rfc-v1.md),
[Möbius and signed sums](mobius-divisor-sum-foundations-rfc-v1.md).
These frozen authoring reports retain their original verification stage;
the integrated checkpoint records the completed closures below.

## Complete proof evidence

Every bundle has been checked in its entirety by the original HA checker and
the independently compiled Lean checker. Reused historical bodies are exact
target/ordered-premise matches; all bodies, including inherited ones, are
checked again. Four inherited signed-sum prerequisites absent from the
available provider bundles were reconstructed from their ordinary scripts.

The source-pinned, deterministic audit record is
[`artifacts/bottom-layer-checkpoints-v2.json`](artifacts/bottom-layer-checkpoints-v2.json).
Its hashes are provenance, never mathematical inferences. The actual bundles
are independently usable:

- [Euler units](artifacts/bottom-layer-euler-units-proof-bundle-v2.json), 571,540 bytes.
- [Prime fields](artifacts/bottom-layer-prime-fields-proof-bundle-v1.json), 594,304 bytes.
- [Möbius values](artifacts/bottom-layer-mobius-values-proof-bundle-v1.json), 813,004 bytes.
- [Signed sums](artifacts/bottom-layer-signed-sums-proof-bundle-v1.json), 855,381 bytes.

Seven principal roots were additionally materialized and rechecked as
ordinary empty-context HA certificates, with no trusted theorem-reference
node or library admission:

| Root | Ordinary proof nodes |
| --- | ---: |
| `euler_theorem_for_units` | 17,918 |
| `euler_coprime_totient_power` | 17,610 |
| `prime_field_of_prime_order_exists` | 15,167 |
| `mobius_value_exists_unique` | 20,227 |
| `mobius_fresh_prime_negates` | 18,203 |
| `divisor_signed_table_reindex_exists` | 8,917 |
| `divisor_signed_sum_permutation_invariant` | 16,872 |

The compiled checker is pinned by exact binary SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`
and size 106,787,344 bytes. This tranche uses the existing binary; it neither
rebuilds the Lean companion nor claims that its current source toolchain
file identifies the older binary's build. Acceptance means an independent
compiled Lean check of the HA certificate, not an automatic mathlib theorem
or a changed logical foundation.

## Definitions and local proof explorers

All 284 historical reviewed definitions retain their literal identities and
records. The 34 new definitions ND0228–ND0261 produce **318 reviewed
definitions, 645 expansion edges and maximum definition layer 12**.

Exact duplicate checks deliberately reuse:

- ND0023 `CanonicalModularResidue` for prime-field reduction.
- ND0141 `IdentityMatrixSelector(b,c,p)` for the p-entry enumeration.
- ND0058 `MatrixMinorFourCode` for generic four-parameter signed-table packing.

The old names are preserved even where the encoded data has a broader new
use. `Unit` remains distinct from the old nonzero-residue range. Existing
`Phi` and `UnitCount` are explicitly included in readable Euler notation.
Every new theorem statement and every local tactic proposition has an exact
defined-to-primitive AST roundtrip. Compound arguments, large numerals,
full-context capture and genuine expansion-edge occurrence are tested.

The [local proof library](../../book/_static/constructive-bottom-layer-explorer/index.html)
provides the original Quadratic Reciprocity layout, exact and defined
theorem pages, and separate proof, notation-use and definition-expansion
arrows. The historical public renderer requires Alpha-admission flags, so a
narrow additive local renderer preserves its structure and byte-identical
assets while replacing authority validation and wording. No false Alpha
flags are passed to that renderer. Local navigation links the four families
to the existing global campaign; published campaign statuses are untouched.
The removed duplicate slots EU0003 and EU001C are reserved, so every surviving
Euler tag, including EU0022, is unchanged. A local-only enhancement wires the
dashboard layer filter alongside search/kind, and new defined proof-line
anchors match the unchanged canonical highlighting script.

## Reproducibility and hostile-evidence checks

From the worktree root:

```sh
PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc python3 scripts/check_constructive_bottom_layers.py --check
```

The command freshly verifies all four HA/Lean bundles and all seven ordinary
roots before comparing the deterministic audit record. It keeps the original
170/175-second authoring CPU guard, 180-second wall alarm and 1,536-MiB RSS
ceiling. All proof, formula, sharing, batch, catalogue and service limits are
unchanged. Complete exports peaked below 1.2 GB; combined v2 seven-root
verification used 388,988,928 bytes peak RSS. The streamlined Euler v2 export
rechecked the complete old seed before exact reuse and finished in 2.725
seconds at 472,301,568 bytes peak RSS.

Independent review and executable negative tests cover forged compiler and
interner output, malformed dependency graphs, poisoned inherited bodies,
source changes, cached factory relabelling, wrong Lean results, invalid
payloads, and oversized or noncanonical audit sidecars. Exact ordered
specification pins bind names, statements, premises, scripts and summaries.
Lean receives the same authenticated bytes as HA through an exclusive
private temporary snapshot. Receipt comparison is bounded and byte-exact;
resource checks precede any exclusive audit-record write.

The focused mathematical suites contain **2,705 passing tests**: Euler 439,
prime fields 1,806, and Möbius/signed sums 460. The current definition,
closure and checkpoint gate adds **671 passing tests**, including the full
170-versus-3,222 AST duplicate audit. The explorer gate adds **278 passing
tests**: **3,654 focused tests in total**. Its 493-file snapshot contains 452
HTML pages, and every exact source statement, local proposition, link,
fragment and inline script is checked. Canonical-JavaScript regressions
exercise getter-only SVG links, all-visible graphs, dashboard filter load
orders, proof-line hash changes and scale navigation.
Numerical examples are diagnostics only and never supply proof authority.

One oversized combined test invocation reached the unchanged wall-time guard;
the individual bounded suites are the regression gates, not a raised timeout.
Live browser interaction was unavailable: the Browser runtime reported no
connected browser, confirmed by empty discovery. Local HTTP checks and
executable canonical-JavaScript/DOM regressions are distinct checks, not a
claim of visual or live-browser inspection.

## Next work and publication boundary

The next exact G007 sequence is masks/append; prime-toggle cancellation;
signed weighting and finite Fubini; convolution; then inversion. Cancellation
and weighting can proceed in parallel after masks. Positive-domain equality
must leave arbitrary input values at index zero unrestricted. Detailed
guards and decomposition are saved in
[PLAN/15](../../PLAN/15_bottom_layer_foundations.md).

The existing compact Alpha v30 catalogue is 66,503,303 bytes, only 605,561
below its unchanged 64-MiB ceiling. Future admission must solve packaging
within the established limits; independently checked local proofs are not
silently promoted. No commits, pushes, deployment, worker restart, hosting
cache change, or modification of the user's unrelated Hydra work occurred.

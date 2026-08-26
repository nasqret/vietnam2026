# Independently checked constructive Kummer closure receipt

Date: **2026-08-25**.

Both original constructive Kummer statements now have complete actual
dependency-closed proof data:

```text
kummer_binomial_carry_bit_count
kummer_carry_free_iff_not_divides
```

Their formulas, hypotheses, witnesses, tactic scripts, and dependency edges are
the exact immutable Alpha-v17 surfaces. No statement was weakened, no axiom or
kernel rule was introduced, and neither theorem acquires Alpha checked-use
authority from this receipt or its independently checked proof bundle.

## Frozen parent and exact transitive closure

| Property | Independently checked value |
|---|---|
| Parent Alpha edition | v17 |
| Parent Alpha identity SHA-256 | `db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4` |
| Parent enrollment SHA-256 | `44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175` |
| Exact dependency theorem rows | `280` |
| Already Stable-closed rows | `171` |
| Already Alpha-closed rows | `11` |
| Existing body-only rows requiring actual closure | `98` |
| Exact theorem dependency edges | `777` |
| Ordered dependency-name SHA-256 | `87c0aa87596f7177836f4171728027e7d372d56214d34e602680f7ddb7d6c881` |
| Ordered 98-row body-only SHA-256 | `50d495e0dff1489e42098198b667c71060bacaf32c2de3b10935129b8f87fd3b` |
| Exact frozen Alpha-v17 surface SHA-256 | `1e0778b0e2415aa6b4f74dd500fe54f00c039f29eab375e080aa7aeec9bbfe34` |

The 98 genuinely unfinished rows have the following dependency-ready waves:

```text
35 → 14 → 7 → 7 → 6 → 7 → 6 → 4 → 2 → 1 → 1 → 2 → 1 → 1 → 1 → 1 → 1 → 1
```

All 175 already checked parent bodies that occur in the complete
quadratic-reciprocity or supplementary-law artifacts are reused only after
those entire artifacts have been independently accepted by the original kernel.
Seven other already-checked parent bodies are reconstructed from their exact
original scripts:

```text
mul_lt_mul_succ_left_nonzero
zero_remainder_implies_multiple
multiple_has_zero_remainder
one_multiple
multiple_decidable_nonzero
multiple_decidable
add_shuffle_middle
```

Six of these rows are Stable-closed; `add_shuffle_middle` is Alpha-closed.
Consequently, the builder constructs **105** actual dependency-curried proof
bodies: 98 genuinely body-only rows and seven previously checked rows whose
local bodies were absent from the reusable artifacts.

Every construction microbatch contains at most 16 proofs, at most 125,000
structural proof nodes, and at most 25,000 proof objects. In particular, the
old 125,454-node naive valuation-composition obstruction disappears because the
complete graph shares each actual predecessor proof body once.

## Exact endpoints and ordinary original-kernel proofs

| Exact theorem | Local node | Statement SHA-256 | Ordinary empty-context proof nodes |
|---|---:|---|---:|
| `kummer_binomial_carry_bit_count` | `277` | `f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f` | `23564` |
| `kummer_carry_free_iff_not_divides` | `279` | `ed30b756bd9703193020ae395a87f1f32a12859d2b9df8fbb79708e9bed2dc00` | `24170` |

The second root genuinely depends on the first. One additional synthetic node
with ID `280` and dependencies `(277, 279)` nevertheless exposes both exact
endpoints explicitly as a constructive conjunction. Its complete ordinary body
is:

```text
ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))
```

This synthetic conjunction has no enrollment, theorem-library identity,
checked-use authority, or axiom status. Both real endpoints are additionally
compiled into ordinary existing `Cut` proofs and independently accepted by the
unchanged kernel from the empty context:

```text
check((), exact_certificate, _closed_formula(exact_original_statement)) = True
```

Both resulting certificates satisfy the existing 125,000-node/25,000-object
policy without raising any resource limit.

## Complete canonical proof artifact

```text
research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json
```

```text
format:                 peano-lab-bundle-v1
bytes:                  1528814
SHA256:                 49fd86708fe5b289d0159526285e73b2aea008c26e0eb41ae8a053c970d4210e
theorem nodes:          280
synthetic conjunction:  1
total graph nodes:      281
dependency edges:       779
actual body-proof nodes:19062
original-kernel checks: 281
conjunction root ID:    280
```

Every theorem formula, every dependency, and every ordinary local constructive
proof tree appears in the artifact. A file hash, theorem name, provenance
record, or this receipt is never accepted as proof.

## Independent replay and Lean verification

From the repository root:

```console
shasum -a 256 research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json
```

Expected:

```text
49fd86708fe5b289d0159526285e73b2aea008c26e0eb41ae8a053c970d4210e
```

The independently compiled Lean proof-bundle verifier checks the complete
artifact without trusting the Python implementation:

```console
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json
```

Actual result:

```text
ACCEPT  research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json  nodes=281  root=280
```

The exact surface, all microbatch resource limits, actual Python-kernel
acceptance, both ordinary empty-context root proofs, malformed-proof rejection,
and unchanged Alpha-v17 release evidence are audited by:

```console
cd peano-lab/py
python3 -m pytest -q tests/test_kummer_complete_closure.py
```

Rebuild identical complete proof data into a previously nonexistent destination:

```console
cd peano-lab/py
python3 -m peano_lab.library.kummer_complete_closure \
  --export /private/tmp/kummer-proof-bundle-v1.json
```

The builder refuses to overwrite an existing file and rejects altered immutable
parent rows, altered theorem formulas, changed dependency edges, missing actual
proofs, false proof bodies, unsafe microbatches, changed conjunction endpoints,
and noncanonical or mutated artifact bytes.

**Release boundary:** immutable Alpha v17 still classifies both endpoint
theorems, and all 98 original body-only dependencies, as `body_checked`.
Neither Stable nor Alpha checked-use membership changes. Any future promotion
requires its own independently reviewed, dependency-closed immutable release.

# Lower-layer continuation: 125 new complete proofs

Date: 2026-08-29. This subsequent implementation is **local, not an Alpha or
Stable promotion and not part of the preceding 126-proof website upload**.
The published base is `ba9a8815395196fdcb9bdd560e9071ca75b4754f`; see the
[separate deployment receipt](lower-tier-publication-receipt-2026-08-29.md).
The new work follows [PLAN/17](../../PLAN/17_rectangular_sums_divisor_involutions_polynomial_products.md).

## Mathematical outcome

Six new ordinary-HA modules supply 125 genuinely new statements:

| Chapter | New theorems | Direct declared dependencies | Tactic commands |
| --- | ---: | ---: | ---: |
| Complementary divisors and finite involutions | 12 | 34 | 480 |
| Möbius divisor cancellation | 28 | 99 | 1,569 |
| Actual signed rectangular sums and finite Fubini | 32 | 92 | 1,393 |
| Prime-field polynomial products and represented degree | 53 | 123 | 2,496 |
| Total | 125 | 348 | 5,938 |

Every statement is AST-distinct from all 3,518 previous statements and every
other new statement. The comparison uses canonical formula-DAG bytes, not
theorem names or a source-string heuristic. Alpha's 3,222 entries, the first
170 research proofs, the next 126 and these 125 remain separate inventories.
Inherited proofs are real checked bodies, never assumed lemmas or new results.

The exact contracts and frozen authoring evidence are documented in:

- [Complementary divisors](divisor-involution-rfc-v1.md).
- [Möbius divisor cancellation](mobius-divisor-cancellation-rfc-v1.md).
- [Rectangular sums and Fubini](signed-rectangular-sums-rfc-v1.md).
- [Polynomial products and degree](prime-field-polynomial-convolution-rfc-v1.md).

The first three RFCs retain their original conditional-body evidence boundary.
The complete-bundle and ordinary-certificate checks below are subsequent
evidence; the historical RFC wording is not silently promoted into a receipt.

## Complete proofs and exact support

All four actual complete bundles passed the unchanged original HA checker
and the independently compiled Lean checker. Both checkers received the same
authenticated bytes; Lean read a private exclusive snapshot, not a mutable
source pathname. All twelve selected principal theorems additionally compiled
to ordinary empty-context HA certificates and passed another exact
specification/formula comparison and original-kernel certificate check.

The final bounded `python3 scripts/check_constructive_lower_continuation.py
--write` also passed all four complete checks, all twelve ordinary roots and
the whole-tranche novelty audit. The deterministic
[machine-readable audit](artifacts/lower-continuation-checkpoints-v1.json)
is 19,846 bytes, SHA-256
`c665db9d1edb12670c1719c00c645eb5eec388e381fb87d9cf4723cbc99314ee`.
Its largest observed resident-memory peak across the fresh workers and
controller was 516,931,584 bytes, below the unchanged 1,536 MiB ceiling.

The final `make -j1 check-constructive-lower-continuation` reran all five
windows and matched the saved audit byte-for-byte. It passed in 263.06 seconds
of aggregate scheduling time, with maximum observed RSS 504,872,960 bytes.
Each individual worker retained its original 180-second wall limit; the
aggregate time is not the duration of a single proof window.

| Bundle | New owned | Prior 170 support | Prior 126 support | New cross-track support | Alpha support | Nodes incl. packaging | Edges incl. packaging |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Divisor involutions | 12 | 0 | 0 | 0 | 127 | 140 | 355 |
| Möbius cancellation | 28 | 41 | 31 | 0 | 276 | 377 | 1,081 |
| Rectangular sums | 32 | 14 | 12 | 0 | 158 | 217 | 551 |
| Polynomial products | 53 | 10 | 2 | 0 | 144 | 210 | 503 |

Importing a Python tactic-string helper does not create a mathematical proof
dependency. In particular, the cancellation source uses authoring helpers
from the involution module but none of its twelve theorem names as premises.
There is no invented cancellation-to-involution proof arrow. The exporter
also reconstructed one inherited Alpha body absent from the available seeds;
that old theorem is included as support and is not a twenty-ninth new
cancellation result. Every reused seed was itself checked before reuse.

Exact complete artifacts:

- [Divisor involutions](artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json):
  292,245 bytes; 7,711 body-proof occurrences; SHA-256
  `deffb1e384e64cd2cb56b4c1603a0fdde7578cec15e80618f5b06197fabf6fed`.
- [Möbius cancellation](artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json):
  2,498,683 bytes; 27,012 body-proof occurrences; SHA-256
  `f858f6bd9e09d6ec33b48689b385222153ad9d326eccb8239ac5776b39955542`.
- [Rectangular sums](artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json):
  2,151,122 bytes; 12,534 body-proof occurrences; SHA-256
  `a6f62d8a0c89431b3596a0d15278643da6981afe166107cdc6aefa5433485395`.
- [Polynomial products](artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json):
  745,307 bytes; 11,604 body-proof occurrences; SHA-256
  `55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3`.

The unchanged independent Lean executable is 106,787,344 bytes, SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`.
It was not rebuilt, and no compiler version is inferred from current files.

| Principal theorem | Ordinary certificate occurrences |
| --- | ---: |
| `positive_divisor_quotient_exists_unique` | 832 |
| `positive_divisor_involution_exists` | 10,740 |
| `divisor_complement_prefix_involution` | 1,810 |
| `mobius_divisor_sum_cancellation` | 36,537 |
| `mobius_divisor_sum_cancellation_exists` | 37,429 |
| `mobius_divisor_sum_cancellation_on_positive_values` | 38,137 |
| `signed_rectangular_slice_exists_extensionally_unique` | 10,224 |
| `signed_rectangular_fubini` | 17,146 |
| `signed_rectangular_row_major_fubini` | 17,334 |
| `prime_field_polynomial_convolution_exists_unique` | 10,055 |
| `prime_field_polynomial_convolution_outside_zero` | 2,887 |
| `prime_field_polynomial_convolution_represented_degree_exists` | 12,260 |

The largest observed bundle-authoring job was Möbius cancellation, with peak
RSS 857,440,256 bytes. Its complete HA/Lean/three-ordinary-root check passed
in 70.39 seconds with 440,844,288 peak resident bytes. Original authoring
windows remain 170/175 CPU seconds, 180 wall seconds and 1,536 MiB RSS.
An initial monolithic four-family/twelve-root audit hit its CPU ceiling
(exit 152) and produced no success record. This is a scheduling boundary,
not permission to enlarge limits or skip an ordinary certificate.

The durable audit runner now uses five sequential fresh workers: an exact
125-versus-3,518 novelty check, followed by four complete family checks with
all three ordinary roots each. Every worker retains the original 170/175 CPU,
180 wall-second and 1,536 MiB policy. The controller retains the same CPU/RSS
ceilings; its 185-second child timeout includes cleanup, and its derived
1,105-second scheduling deadline covers the five separate windows plus its
own metadata work. This scheduling deadline is not a larger proof window.

Only bounded canonical messages from the newly launched workers are accepted.
Nonces, current source/specification/parent/checker bindings, actual bundle
metadata, exact root identities and all support roles are checked. Changes
between the start and end of the run fail closed. No stored success record
supplies proof authority; `--write` remains exclusive and `--check` performs
fresh verification before exact saved-byte comparison. The original
`verify_checkpoint` function is byte-identical to the reviewed baseline.

## Conservative definitions and exact mathematical boundaries

Nineteen definitions, ND0281–ND0299, preserve all 337 earlier definition
objects and graph records. The full registry has **356 definitions, 742
genuine expansion arrows and maximum zero-based layer 12**. Existing
`FpMul`, `BetaPrefixEqual`, `ArithTableEqual`, residues, sums, beta tables and
signed operations are reused. Formula compaction round-trips the complete
first-order AST, including repeated/compound arguments under binders.

Important domain and representation distinctions are retained:

- Complementary-divisor totality and reversibility require positive `n`.
  Prefixes exist at every length, but the proved finite permutation has
  length `S n`, not an arbitrary truncated length.
- Divisor prime-toggle closure uses `Prime(p)`, `n>0` and `p | n`.
  The graph itself does not assume Möbius negation or cancellation.
- Möbius cancellation concerns actual positive divisors. The input `F(0)`
  may be arbitrary because the actual divisor mask excludes it. Signed code
  `2` means `+1`; the sum is `+1` at `n=1` and zero at `n>1`.
- Signed Fubini uses actual entries `F((o+s*i)+t*j)` and actually constructed
  slices/row tables. Zero dimensions and zero strides are allowed. Uniqueness
  concerns represented values, not arbitrary beta encodings.
- Polynomial coefficients are highest-degree-first, with explicit lengths.
  The full antidiagonal window is `S i`; convolution takes its actual sum and
  canonical residue. Empty inputs give an empty product. The tail-zero result
  concerns the convolution coefficient, not unconstrained beta entries past
  the stored prefix.
- Represented degree requires an actually decoded nonzero leading coefficient.
  It does not normalize leading zeros or assign a degree to the zero polynomial.
  The degree-addition theorem retains its prime-field hypotheses.

## Local integration and reproduction

The [new local explorer](../../book/_static/constructive-lower-continuation-explorer/index.html)
has four canonical Quadratic Reciprocity-style families, with DI/MC/RS/PC
tags, exact and defined readers, mixed theorem/definition maps, complete
bundles, literal sources and links to both older research generations.
It uses the unchanged model renderer and assets. Definition-use arrows and
definition-expansion arrows are distinct from actual theorem dependencies;
reachability and proof paths use proof edges only.

The snapshot contains 395 files, including 358 HTML pages. The 394 payload
files total 31,346,852 bytes. The manifest SHA-256 is
`98d78a16815e40281ebf9ef0f4b8b9d183109e5c25960576189e3f5d0c0735a3`;
the checkpoint-inventory digest is
`25c837e9a7eb4f587f40a5d9fc5a8b0af406d91d629a48cc87115a8b2f935091`.
Every payload size and hash matches the manifest. The initial bounded build,
including four fresh HA/Lean checks, passed with 484,491,264 peak RSS bytes.
The final direct `--check` repeated all four proof checks and matched every
snapshot byte, with peak RSS 489,488,384 bytes.

| Local chapter | Definitions displayed | Actual definition-expansion edges | Principal tags |
| --- | ---: | ---: | --- |
| Divisor involutions | 10 | 13 | DI0001, DI000A, DI000B |
| Möbius cancellation | 39 | 71 | MC001A, MC001B, MC001C |
| Rectangular sums | 18 | 34 | RS0007, RS001E, RS0020 |
| Polynomial products | 19 | 30 | PC0029, PC002D, PC0035 |

Shared definitions are not counted again as new identities. The complete
356-definition registry and the smaller chapter-specific displays serve
different purposes and have deliberately different counts.

All 61 distinct explorer regressions passed in 133.86 seconds with peak RSS
507,969,536 bytes. They rechecked the actual complete bundles, every exact
statement/tactic/local proposition, four independently written endpoint
contracts, all links/fragments and the genuine typed DAGs. The actual
canonical JavaScript passed getter-only SVG `href`, filtering and hash-focus
cases; exact-reader navigation was exercised for all 129 theorem/index pages.
These are runtime harness tests, not a claim of visual browser inspection.

Distinct focused regressions passed:

| Group | Passed |
| --- | ---: |
| Complementary divisors and involutions | 84 |
| Möbius divisor cancellation | 169 |
| Actual slices, rectangular sums and finite Fubini | 356 |
| Polynomial convolution and represented degree | 740 |
| New support cones and conservative definitions | 100 |
| Complete checkpoints, inherited-body attacks and ordinary roots | 191 |
| Bounded fresh-worker audit protocol and failure handling | 86 |
| Canonical explorers and actual JavaScript | 61 |
| Browser-shell source/package contract | 20 |
| Unchanged kernel, syntax, cut, formula DAG, bundle and replay controls | 233 |
| Total distinct focused tests | 2,040 |

The 191 checkpoint tests include actual compiled Lean positives for all four
families and all twelve ordinary certificates. They reject poisoned inherited
Alpha/170/126 bodies, wrong targets, omitted/swapped premises and a genuinely
valid certificate returned with the wrong specification or formula. The
largest checkpoint-test window used 129.56 seconds and the largest observed
checkpoint-test RSS was 525,565,952 bytes. The 86 runner tests passed in
35.97 seconds, including one actual fresh complete HA/Lean/three-root worker,
strict novelty/report protocol checks, real signal/timeout/oversized-output
failures and preservation of the old receipt on failed verification. Repeated
runs are not added to these counts. This is not a repository-wide or remote
green-CI claim.

The local browser package now contains 497 Python files and 519 content
manifest entries, application identity `a-e367fe077425`, build `2026-08-29a`.
The complete app-manifest SHA-256 is
`e367fe077425d9685b177119e244df3ef6105b016c73f6fcaa6f5323796af652`.
Worker inventory, manifest, `APP_ROOT` and `PEANOAPPID` checks pass. This new
application and the new four-family explorer are not deployed by this batch.

The exact deterministic snapshots have dedicated checks without adding this
local work to `stage-proofs`:

```sh
make -j1 check-constructive-lower-continuation
make -j1 book-constructive-lower-continuation-explorer
```

## What remains open

Full **G007 Möbius inversion** remains open. Divisor involutions, actual finite
Fubini and Möbius divisor cancellation are now proved components; the next
layer must construct actual Dirichlet convolution, prove its finite
reindexing/associativity and unit identities, and derive the exact inversion
equivalence. Cancellation alone is not that full equivalence.

Full **G091 general prime-power fields** remains open. Coefficient convolution,
finite support and represented degree addition are now proved components.
Evaluation-product compatibility, polynomial division and gcd, irreducible
construction, and the extension-field construction require further proofs.

Alpha remains v30 with 3,222 checked-use entries and the unchanged catalog
SHA-256 `ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Stable remains 432. No proof, formula, replay, bundle, catalog or service
limit changed. No production cache headers, Peano channel, gateway, mailbox
or running Lean worker changed. Unrelated Hydra worktrees were untouched.
No visual-browser or repository-wide/remote-CI green result is claimed.

# Alpha v26 first-wave proof-closure receipt

Date: 2026-08-27.

The complete self-contained proof bundle was accepted by both the unchanged
original intuitionistic arithmetic kernel and the independently compiled Lean
bundle verifier. This receipt describes actual ordinary proof bodies and their
complete dependency graph; neither the receipt nor its hashes constitute proof
authority on their own.

## Exact additive theorem inventory

The parent is the unchanged 2,080-theorem Alpha v25 edition. Its identities are:

```text
edition:    3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28
enrollment: f724872707cdcf401f35cb69680e1bbec86d626c4bf56e6d41f01a3724e2be81
```

The new frontier contains 58 theorems and 218 actual direct dependency edges:

| Campaign | Theorems | Edges | Tactic commands | Body-proof nodes |
| --- | ---: | ---: | ---: | ---: |
| Coprime natural square factors | 9 | 48 | 408 | 931 |
| Positive primitive Pythagorean classification | 23 | 77 | 733 | 1,335 |
| Unconditional Fermat exponent four and descent | 26 | 93 | 852 | 1,515 |
| Total | 58 | 218 | 1,993 | 3,781 |

The exact new ordered-name SHA-256 is
`226cc91137521e0484dc6c3dcf90d2138e67acc79bf53798d84fb0deaf5973de`.

These additions give 2,138 checked-use theorem entries while preserving all
432 Stable entries. The resulting 1,706 Alpha-only entries do not silently
change Stable membership or authority.

## Actual closed proof cone

The canonical artifact is
`research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json`.

```text
real theorem bodies:       215
new theorem bodies:         58
historical theorem bodies: 157
maximal theorem endpoints:   4
synthetic conjunctions:      1  (not a library theorem)
total bundle nodes:        216
real dependency edges:     554
bundle edges:              558
structural body nodes:  10,397
original kernel calls:     216
artifact bytes:        364,186
root node:                 215
SHA-256: 59afca707b33b68df907c941683e335492f7de12ee3888219339c5dfce8ec4fc
```

The exact ordered real-cone-name SHA-256 is
`042e885b14e221f86cc724a815af4069dabffef18cac71425e54f6f7c4c1d0dc`.

Historical bodies are drawn from the smallest applicable frozen providers:

| Provider | Real bodies retained |
| --- | ---: |
| Alpha v19 frontier | 65 |
| Alpha v21 advanced layer | 5 |
| Alpha v22 transport layer | 1 |
| Alpha v24 research layer | 64 |
| Alpha v25 breakthrough layer | 12 |
| Original parent scripts reconstructed | 10 |

Every retained target and exact dependency list is matched to the immutable
parent specification, and every retained ordinary body is independently
rechecked. No theorem receipt, external theorem name, or historical hash is
accepted in place of its actual proof.

## Main mathematical endpoints

| Node | Exact theorem |
| ---: | --- |
| 163 | `coprime_square_product_factors` |
| 165 | `square_divides_square_root` |
| 188 | `pythagorean_positive_primitive_classification` |
| 207 | `fermat_four_strict_descent_proved` |
| 208 | `fermat_four_no_square` |
| 209 | `fermat_four_no_fourth` |
| 213 | `fermat_four_complete_classification` |
| 214 | `fermat_four_positive_sum_not_square` |

Nodes 188, 209, 213, and 214 are the four actual maximal endpoints. Node 215
only packages their conjunction and is not enrolled as another theorem.

The primitive Pythagorean theorem proves both directions of the positive
classification, with both leg orientations and actual ordered, coprime,
opposite-parity Euclid parameters. The Fermat descent is an actual constructed
strictly smaller counterexample, not a premise left for future work. Its exact
G078 endpoint is:

```text
forall x y z.
  ~(x=0) -> ~(y=0) -> ~(x*x*x*x + y*y*y*y = z*z)
```

There is no positivity assumption on `z`. The stronger complete natural
fourth-power classification identifies exactly the trivial solutions:

```text
a^4+b^4=h^4  iff  (a=0 /\ b=h) \/ (b=0 /\ a=h).
```

All exponents and named relations in this presentation are expanded to the
unchanged language `{0,S,+,*,=}` in the actual accepted artifact.

## Independent Lean acceptance

The compiled verifier was run on the exact canonical file:

```text
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json

ACCEPT  research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json  nodes=216  root=215
```

This acceptance covers all 216 ordinary bodies and every local dependency
edge. It does not rely on a Lean axiom postulating any new number-theory result.

## Memory bounds and reproducibility

Historical certificates are decoded one at a time. Only the 147 required
historical bodies are retained, and 10 missing historical bodies plus the 58
new bodies are reconstructed in bounded batches. The default batch size is
one; the allowed maximum is 16. Existing caps of 125,000 proof-node occurrences
and 25,000 actual immutable proof objects per batch are unchanged.

The new closure correctly distinguishes proof-object identity count from
proof depth. A local regression test detects the historical tuple-unpacking
mistake that mislabeled depth as object count; no historical source or sealed
artifact was modified. Tests additionally cover shared objects and exhaustion
of an accumulated two-body object budget.

Both batch size one and batch size 16 reconstruct byte-identical canonical
proof bundles with the SHA-256 above. At batch size 16, the largest actual
batch has 1,057 nodes and 1,057 immutable proof objects, comfortably inside
the unchanged caps.

## Verification tests

The 87 square-foundation tests and 18 full-closure tests pass together
(`105 passed`). They include all exact square statement seals, rejection of
each of the 48 individually removed square-proof dependencies, false
conclusions and truncated bodies, zero boundaries, every complete-bundle
ordinary body, altered theorem edges, false targets, forged packaging roots,
missing/unsealed artifacts, and the memory-accounting regressions.

The candidate-specific inverse and Fermat suites separately report 86 and 95
passing tests. Numerical examples in those suites are regression checks only;
the self-contained original-kernel and Lean-accepted artifact is the proof
evidence.

# Alpha v30 Gaussian unique-factorization proof receipt

Date: 2026-08-28. This records observed complete proof and runtime checks,
not a new axiom, inference rule, or proof-by-hash.

## Canonical complete artifact

```text
research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json

new theorem bodies:             180
inherited theorem bodies:       272
actual theorem bodies:          452
maximal endpoints:               18
conjunction packaging nodes:      1  (not a library theorem)
total bundle nodes:             453
ordinary dependency edges:     1430
total bundle edges:            1448
structural body occurrences:  39423
original kernel calls:          453
root node:                      452
artifact bytes:             6143166
artifact SHA-256:
e0e10f11c5b12b411843054000a77be22ede7db53602814f9532e3e7c8daa270
actual-cone ordered-name SHA-256:
fe63423af323582ebbe7f05c2bd3848a3717ac5b83bb0de35913789c517ac35f
```

The exact parent is the unmodified 3,042-theorem Alpha v29 catalogue,
SHA-256 `2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0`.
The additive inventory contains 3,222 checked-use entries, 10,588 actual
theorem edges and 53 layers. Stable remains the object-identical default 432.

```text
v30 edition identity:
8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9
v30 ordered enrollment:
04b73a38d04d1bd8038c1712b7f4f6cc77156f97a890515524761bb1cdf71393
```

The full G082 root is `gaussian_unique_prime_factorization`, statement
SHA-256 `57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219`.
It constructs actual finite Gaussian prime factorizations and a genuine
unit-matching beta permutation for every other factorization. It does not
assert literal uniqueness of leading units or prime representatives.

## Frozen mathematical work

Seven frozen factories contribute 180 theorem bodies, 673 declared actual
dependency edges and 7,859 ordinary tactic commands. Their bodies have
15,270 structural proof-node occurrences. The sum of the per-body distinct
object counts is 15,083; this is not a globally deduplicated memory count.
The largest individual body has 827 nodes; maximum body depth is 83.

The focused mathematical suites passed 3,685 tests:

| Component | Tests | Observed seconds |
| --- | ---: | ---: |
| Ring, divisibility and gcd/prime foundations | 919 | 546.82 |
| Finite divisor search | 442 | 199.29 |
| Actual finite products and factorization existence | 1197 | 260.80 |
| Actual Gaussian product reindexing | 42 | 167.00 |
| Unit/permutation uniqueness, including two concrete input instances | 1085 | 661.62 across three bounded groups |

All 180 dependency-curried bodies passed the original kernel. Independent
tests cover exact public formulas, all generated and nested legacy binders,
compound terms and large numerals, actual beta entries and product histories,
all four units, zero exclusion, repeated associates, and hostile proof or
premise mutations. Finite integer models are diagnostic examples, not proof
authority. The full closure below is a separate, stronger integration gate.

## Resource-bounded authoring and full composition

The original single-process attempt reached the unchanged CPU limit, and
some larger authoring batches likewise exhausted a time window. No limit
was increased and no failed mathematical check was accepted. Work was split
into actual self-contained proof checkpoints in fresh processes.

| Checkpoint | New rows | Bundle nodes | Edges | Body occurrences | Bytes | Seconds | Peak resident bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ring and divisibility | 94 | 272 | 780 | 24402 | 2917840 | 87.412 | 846446592 |
| Through complete finite search | 131 | 322 | 979 | 27898 | 4012681 | 148.470 | 863043584 |
| Through actual factorization existence | 159 | 410 | 1267 | 33681 | 5404477 | 108.556 | 496943104 |
| Through product reindexing | 162 | 414 | 1293 | 34336 | 5561076 | 107.220 | 825065472 |
| Through the first twelve permutation helpers | 174 | 447 | 1421 | 38237 | 6112729 | 97.755 | 799588352 |
| Complete G082 candidate, freshly checked | 180 | 453 | 1448 | 39423 | 6143166 | 56.068 | 776142848 |
| Canonical export, freshly checked again | 180 | 453 | 1448 | 39423 | 6143166 | 37.101 | 628408320 |

The largest induction row, `gaussian_irreducible_products_associate_unique`,
has 24 ordered prerequisites, 348 commands and an 827-node body of depth 74.
It was authored separately using the unchanged ordinary tactic reconstruction
and `checked_final`. The output was one ordinary closed implication with
those exact 24 prerequisite formulas as antecedents. This conditional proof
is not, by itself, an unconditional factorization theorem.

```text
conditional checkpoint: one node, zero dependency edges, 827 body nodes
conditional checkpoint bytes: 877945
conditional checkpoint SHA-256:
ad9953dcb6df071521d83630c46fb4ccff7b30bd7d18cbde814fb16a484a8e07
authoring: 170.88 wall seconds; 163.25654 CPU seconds
authoring peak resident bytes: 1038680064
fresh separate original-kernel and compiled-Lean check:
ACCEPT, one node, root zero; 3.376 seconds; 380403712 peak resident bytes
```

A fresh composition process fully checked the 447-node checkpoint, decoded
and checked the conditional proof, and matched its entire ordered implication
target against the frozen theorem and all 24 exact prerequisite statements.
It used that unchanged ordinary body with the genuine proved prerequisite
nodes, reconstructed the remaining five ordinary bodies, and submitted all
453 resulting nodes and all ordered edges to the original kernel. This was
proof-data composition, not a new trusted rule or a bypass of any premise.

The canonical export was then generated by the standard checked exporter,
not copied. It freshly checked all 453 seed nodes, retained all 452 exact
theorem bodies, rebuilt the exact dependency graph and packaging root,
checked all 453 output nodes again, and used exclusive file creation.
All 19 immutable historical proof-provider byte pins were checked, including
providers unnecessary for the final combination.

Only the canonical combined artifact is required by the release. Permanent
tests project every authoring checkpoint and the one-node conditional proof
back out of canonical proof data, check them again, and compare the exact
original payload bytes. No temporary checkpoint path is runtime authority.

All authoring and composition processes used the existing 170/175-second
CPU bounds and a 180-second wall alarm. Ordinary authoring batches contained
one row. The original proof, term, formula, annotation, sharing and bundle
limits remained unchanged. Peak values above are measured local process
observations, not browser memory guarantees.

The final artifact can be reproduced without any temporary authoring file:

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc python3 \
  -m peano_lab.library.campaign_gaussian_factorization_closure \
  /private/tmp/v30-gaussian-rebuilt-proof-bundle.json --batch-size 1 \
  --seed-bundle research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json
```

The destination must not already exist. The seed and reconstructed output
are independently checked; exporting proof data does not enroll a theorem.

## Single ordinary empty-context certificate

The first unchanged layer compiler produced validly bounded ordinary syntax,
but its full kernel traversal exhausted the existing CPU window. Profiling
located repeated shifts of large, irrelevant closed layer contexts beneath
term binders. The kernel and all limits remain unchanged. The new untrusted
provider hoists the original closed conditional proofs into actual ordinary
implication arguments and performs only binder-free wiring in the temporary
layer context. Every supplied argument is proved, and every temporary premise
is discharged before the final public theorem is checked in the empty context.

The full prototype checked the whole 453-node canonical artifact, every one
of the 429 conservatively interned bodies in the principal root's actual cone,
and the final exact original-kernel theorem. It passed in **50.970 seconds**,
with **514,916,352 peak resident bytes**, under the same 170/175 CPU seconds,
180-second wall alarm and 1,536 MiB observed-process memory bound.

The integrated production regressions then passed in separate fresh bounded
processes, with an explicit peak-memory assertion:

| Actual production path | Seconds | Peak resident bytes |
| --- | ---: | ---: |
| Canonical provider: full artifact, interned bodies, one ordinary G082 theorem | 52.729 | 588709888 |
| Native `editions_v30.replay` plus a second fresh empty-context check of its returned certificate | 96.306 | 1021362176 |

Both returned the exact 52,094-node ordinary proof and exited successfully.
The second path includes normal edition loading and admission guards; it is
not a metadata-only or mocked runtime test.

The original graph and the transformed ordinary proof have separate, explicit
accounting domains:

| Accounting domain | Actual | Unchanged limit |
| --- | ---: | ---: |
| Actual principal-root graph nodes | 429 | 4096 |
| Original graph formula occurrences, including requested target | 285867 | 500000 |
| Original dependency-layer package formula occurrences | 278584 | 500000 |
| Original dependency-layer package maximum depth | 65 | 256 |
| Conditional argument formula 1 occurrences / depth | 42977 / 52 | 500000 / 256 |
| Conditional argument formula 2 occurrences / depth | 497487 / 72 | 500000 / 256 |
| Conditional argument formula 3 occurrences / depth | 219261 / 87 | 500000 / 256 |
| Entire transformed ordinary proof occurrences | 52094 | 500000 |
| Entire transformed ordinary proof distinct objects | 35123 | 100000 |
| Entire transformed ordinary proof depth | 118 | 256 |
| Entire transformed ordinary proof formula/term annotation occurrences | 2215215 | 5000000 |
| Entire transformed ordinary proof combined envelope depth | 118 | 256 |

There are 759,299 occurrences in the closed conditional formulas before the
conjunction grouping, and 759,725 after grouping. These are additional proof
argument annotations, **not** an expanded graph advertised as satisfying the
500,000 graph or dependency-layer budget. Their annotations are charged twice
for the two formula fields of each identity cut, and those 1,519,450
occurrences are included in the full 2,215,215-annotation candidate envelope.
All other graph target, dependency, original body, individual formula and
transformed proof bounds are checked as well. Nothing is accepted solely
because its digest or a prior conditional receipt matches.

The permanent small multiargument regression checks the exact empty-context
conclusion and rejects omitted arguments, open hypotheses, reversed edges,
swapped logical premises, miswired projections and altered conclusions.
Separate lower-budget regressions enforce both the original graph gates and
the entire transformed candidate envelope. The ordinary theorem contains no
new proof constructor, external proof reference, theorem-name lookup or
undischarged premise. The canonical bundle bytes remain unchanged.

## Independent compiled Lean checks

The actual canonical command was:

```sh
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json
```

```text
ACCEPT research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json nodes=453 root=452
```

It took 0.477 seconds and peaked at 187,498,496 resident bytes. All five
smaller full checkpoints, the isolated conditional proof, and the combined
candidate also passed the compiled verifier.

This executable is the existing Lean **4.28.0** build; it is not a newly
compiled local 4.31.0 binary. Exact provenance was rechecked for this receipt:

```text
binary: ../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify
binary bytes: 106787344
binary SHA-256:
22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033
binary build-trace SHA-256:
46e0668fc6da76c84106f7f95caf2aea5b3eaece14a97d6528327298703de4d5
PeanoLab/VerifyBundle build-trace SHA-256:
9c8c380802aba0f7405a62c6832751303438f51a16d1e2e2bb0f6098eb0465d3
explicit installed compiler version:
Lean 4.28.0, arm64-apple-darwin24.6.0, Release
compiler commit: 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b
```

The companion checkout requests 4.31.0, but that toolchain is not installed
locally. No installation or private repository modification was attempted.
A separate remote 4.31.0 checker build does not establish that this artifact
was checked by that binary. Those claims remain deliberately distinct.

## Final provider and admission regressions

All **227 tests passed**, with no skips or expected-failure exclusions:

| Suite | Passed |
| --- | ---: |
| `test_campaign_gaussian_factorization_closure.py` | 123 |
| `test_library_editions_v30_admission.py` | 104 |

The provider total contains all 94 original closure tests plus 29 additional
hoisting soundness, exact-context, malformed-graph and unchanged-budget tests.
Every canonical authoring checkpoint is reconstructed from only the released
artifact and compared byte-for-byte. The normal edition replay returns an
actual closed certificate, not merely an entry labeled checked.

The 227 cases ran exactly once each in 20 serial fresh-process windows. Every
window used unchanged CPU limits `(170,175)`, a 180-second wall alarm and an
explicit `peak_resident_bytes <= 1536*1024*1024` assertion. Total elapsed time
across those windows, including their process startup and shutdown overhead,
was **557.594 seconds**. The slowest window was the 96.306-second native
ordinary replay plus its independent second kernel traversal. Maximum
observed resident memory across all windows was **1,210,499,072 bytes**;
this occurred during a forged-target artifact test, not ordinary replay.

The suite checks the exact immutable v29 parent and all 19 historical
providers, parent object identity, unchanged Stable membership, all frozen
factory and specification fields, lowercase artifact paths, cold browser
layout and repository-free supplied-parent loading, malformed seals, missing
or changed bytes, and forged bodies, targets, ordered edges and packaging
even when an attacker supplies a matching replacement hash and byte count.
The compiled independent Lean check is included in the admission suite.

A separate read-only peer audit found no logical/context, authority or
acceptance-budget defect in the hoisting compiler. It independently confirmed
the context indices, empty-context argument placement, unchanged original
graph domain, cumulative layer budget and complete doubled-annotation
accounting. Earlier mathematical sources, artifacts, checker code and all
resource limits remain unchanged. This receipt does not claim that remote
publication, deployment or a browser visual test has occurred.

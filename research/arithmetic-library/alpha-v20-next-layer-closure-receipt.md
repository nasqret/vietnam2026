# Alpha v20 next constructive layer: independently checked complete closure

The immutable, completely checked Alpha-v19 parent contains exactly 1,737
theorem specifications. Its frozen enrollment SHA-256 is
`1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795`; its
identity SHA-256 is
`905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7`. Neither
digest grants mathematical authority or silently changes the parent edition.

The next additive constructive frontier consists of **39 genuine new theorem
specifications** in four disjoint campaigns:

```text
polynomial Horner evaluation:         7 theorems
matrix cell / dot product:           10 theorems
Bertrand prime multiplicity / chain: 13 theorems
finite continued fractions:           9 theorems
                                     --
                                     39 theorems
```

Their exact full transitive dependency cone has **550 Alpha-v19 parent
theorems**, plus all **39** new rows: **589 actual theorem nodes** and
**2,033 genuine direct theorem dependency arrows**. The exact ordered theorem
name SHA-256 is
`88865cb1ab2c4d3c463034dcadc21427b9e4f736f67814a6376997dd0abcc256`.

The 12 maximal campaign endpoints are

```text
beta_horner_eval_exists_unique
beta_horner_eval_empty
beta_horner_eval_successor_decompose
beta_matrix_cell_exists_unique
beta_dot_product_exists_unique
beta_dot_product_empty
beta_dot_product_commutative
signed_matrix_two_determinant_exists
signed_matrix_two_determinant_functional
central_binom_prime_divisor_multiplicity_one_exists
iterated_bertrand_prime_chain_exists
continued_fraction_positive_exists
```

Every one of the 589 theorem rows is reachable from at least one of these
endpoints. A balanced ordinary conjunction of the 12 endpoint formulas is
added only as a synthetic local proof-bundle root. The conjunction is not an
enrolled theorem, new axiom, kernel constructor, trusted reference, or
release-authorized checked-use admission.

## Frozen complete constructive proof artifact

```text
research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json

SHA-256:                       1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069
Canonical UTF-8 bytes:         14,775,673
Real theorem proof nodes:      589
Synthetic conjunction roots:   1
Complete proof-bundle nodes:   590
Direct local dependency edges: 2,045
Actual structural proof nodes: 190,533
Independent kernel calls:      590
```

The artifact stores the **entire ordinary intuitionistic proof body at every
local node**, including all 550 parent proofs. No body is replaced by a
historical name, hash, theorem receipt, disk reference, oracle, opaque axiom,
or previously trusted edition membership. Its unchanged proof-bundle checker
validates the full exact graph and calls the original intuitionistic kernel
separately on all **590** dependency-curried bodies.

## Exact parent-body provenance

All reusable parent sources are first bound to their existing frozen byte
counts and SHA-256 digests. Parent source decoding is deliberately performed
one file at a time; only required exact bodies are retained, and temporary
decoded graphs are released before the next source is processed.

| Frozen independent source | Exact reused proof bodies |
| --- | ---: |
| `alpha-v19-campaign-frontier-proof-bundle-v1.json` | 182 |
| `bertrand-proof-bundle-v1.json` | 362 |
| `alpha-v19-residual-proof-bundle-v1.json` | 2 |
| `two-square-proof-bundle-v1.json` | 1 |
| Total embedded reused bodies | 547 |

The exact three checked-parent rows unavailable in these source artifacts are

```text
beta_pointwise_mul_prefix_extend
beta_pointwise_mul_prefix_exists
cell_constructor
```

Each is reconstructed from its actual immutable Alpha-v19 dependency-curried
tactic script and checked again by the unchanged original kernel. The same
procedure reconstructs all **39** genuine new theorem bodies. Thus precisely
**42** ordinary proof bodies are rebuilt and precisely **547** bodies are
reused and embedded, yielding all **589** exact theorem nodes.

The reconstruction ran in seven microbatches of six proofs. The largest
actual batch contained only **596 structural proof occurrences**, and the
largest immutable-object count of any batch was **203**. Every batch remains
far below the unchanged caps of **16 proof bodies**, **125,000 structural
occurrences**, and **25,000 proof objects**. Existing formula, annotation,
proof-depth, decoding, and bundle limits remain unchanged.

Every reused proof is still independently checked as part of the final
self-contained bundle. Frozen source bytes and historical provenance are only
fail-closed transport seals; they never replace an original-kernel check.

## Fail-closed audit

The evidence implementation is

```text
peano_lab.library.campaign_next_layer_closure
```

Its exact public surfaces are

```text
next_layer_closure_plan()
assemble_next_layer_proof_bundle()
check_next_layer_proof_bundle(bundle, target)
checked_next_layer_proof_bundle()
export_next_layer_proof_bundle(output)
```

The focused unchanged-kernel audit is

```text
python3 -m pytest -q tests/test_campaign_next_layer_closure.py

16 passed in 21.74s
```

It independently verifies the immutable parent identity, exact 39-row
frontier, 589-row transitive closure, all 2,033 real theorem dependency
arrows, the four frozen proof-source inventories, all 12 maximal roots,
bounded checked reconstruction of both an old parent and a new theorem,
rejection of invalid microbatch limits, exact canonical artifact bytes,
**590 actual original-kernel checks**, and fail-closed rejection of modified
theorem dependencies, synthetic roots, actual proof bodies, frozen parent
artifact bytes, and missing canonical artifacts.

Separate immutable Alpha-v20 enrollment and release admission remain the
responsibility of the explicitly versioned edition machinery. This receipt,
source annotation, artifact digest, and proof-construction module do not by
themselves promote any theorem or modify Stable or Alpha-v19 authority.

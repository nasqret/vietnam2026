# Alpha and Stable library editions

The arithmetic library has two cumulative editions. **Alpha** is the building
library: every reviewed new layer enters it with an explicit evidence state
while compilation, dependency shape, resource use, notation, and documentation
are still being curated. **Stable** is the promoted subset whose complete
dependency closures and release artifacts have passed the additional admission
gates.

This distinction is about release maturity, not secrecy. Alpha proofs are
ordinary repository material, and many already have stronger proof evidence
than the word “candidate” suggests. Conversely, a tag, a graph node, or a
successful modular-body check does not by itself make a theorem Stable.

```{admonition} The invariant
:class: important
Stable is a subset of Alpha. A Stable theorem keeps the same statement,
dependencies, name, and proof identity in the Alpha view. Promotion changes
release membership; it does not silently replace the mathematics.
```

## What is canonical today

The repository now has canonical machine-readable artifacts for both
editions. Stable v1 remains sealed at 432 rows, Alpha v1 remains sealed at 885
rows, Alpha v2 remains sealed at 902 rows, and Alpha v3 remains sealed at 923
rows. Alpha v4 remains sealed at 965 rows, Alpha v5 remains sealed at 972
rows, Alpha v6 remains sealed at 993 rows, and Alpha v7 remains sealed at
1,017 rows. Current Alpha v8 preserves the entire v7 enrollment ledger
exactly, then appends thirty-eight reviewed Bertrand rows at indices
1017--1054. Its two frozen dependency-topological microbatches contain 24
recurrence-defined `Choose` and baseline `CentralBinom` rows, followed by 14
central recurrence, factorial bridge, growth, seed, and lower-bound rows. The
initial Stable prefix is a historical fact about these channels, not the
permanent promotion rule.

| Surface | Exact scope | What the count means |
|---|---:|---|
| Stable catalog and theorem atlas | **432** theorems | complete registered, empty-context-checked library |
| Sealed Alpha v1 catalog | **885** theorems | immutable parent: 432 Stable plus 453 Alpha-only rows |
| Sealed Alpha v2 catalog | **902** theorems | immutable parent: 432 Stable plus 470 Alpha-only rows |
| Sealed Alpha v3 catalog | **923** theorems | immutable parent: 432 Stable plus 491 Alpha-only rows |
| Sealed Alpha v4 catalog | **965** theorems | immutable parent: 432 Stable plus 533 Alpha-only rows |
| Sealed Alpha v5 catalog | **972** theorems | immutable parent: 432 Stable plus 540 Alpha-only rows |
| Sealed Alpha v6 catalog | **993** theorems | immutable parent: 432 Stable plus 561 Alpha-only rows |
| Sealed Alpha v7 catalog | **1,017** theorems | immutable parent: 432 Stable plus 585 Alpha-only rows |
| Current Alpha v8 catalog | **1,055** theorems | 432 Stable plus 623 Alpha-only rows |
| Alpha checked-use subset | **570** theorems | 432 `stable_closed` plus 138 `alpha_closed` rows |
| Alpha v8 proof graph | **3,224** edges / **45** layers | exact direct dependencies for all 1,055 enrolled rows |
| Quadratic-reciprocity Alpha slice | **557** specifications | 241 Stable prerequisites and 316 Alpha-only specifications |
| Stable $\cup$ QR slice | **748** distinct theorem names | 432 Stable plus the 316 QR Alpha-only rows |
| K3B focused map | **41** nodes | 12 Stable prerequisites, 22 Alpha-only theorem/support nodes, and 7 conservative definitions |
| K3B cold-closure receipt | **17** selected roots | two deterministic empty-context WMI passes, all with zero DNE |
| K3C additive tranche | **17** specifications | indices 885--901, all `body_checked`, cold receipt pending |
| Bertrand first-round tranche | **21** specifications | indices 902--922, all `body_checked`, cold receipt pending |
| Bertrand Round-2 tranche | **42** specifications | indices 923--964, all `body_checked`, fail-closed |
| Bertrand `FactorialVal` tranche | **7** specifications | indices 965--971, all `body_checked`, fail-closed |
| Bertrand Alpha-v6 tranche | **21** specifications | indices 972--992 in an exact 8+5+5+3 split, all `body_checked`, fail-closed |
| Bertrand Alpha-v7 tranche | **24** specifications | indices 993--1016 in an exact 3+5+4+2+5+3+2 split, all `body_checked`, fail-closed |
| Bertrand Alpha-v8 tranche | **38** specifications | indices 1017--1054 in exact 24+14 microbatches, all `body_checked`, fail-closed |

For comparison, the sealed Alpha v1 proof graph has **2,641** edges / **45** layers,
and its evidence partition was 432 `stable_closed`, 138 `alpha_closed`,
314 `body_checked`, and one `pending_layered_closure`. Its immutable machine
surfaces remain `artifacts/peano-library/channels.json` and
`artifacts/peano-library/alpha/catalog-v1.json`; Alpha v2 through v8 are
additive children, not in-place rewrites of either file.
The sealed Alpha v3 graph had **2,730** edges / **45** layers and 352 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v3.json`.
The sealed Alpha v4 graph had **2,891** edges / **45** layers and 394 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v4.json`.
The sealed Alpha v5 graph had **2,912** edges / **45** layers and 401 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v5.json`.
The sealed Alpha v7 graph had **3,072** edges / **45** layers and 446 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v7.json`.

The canonical Alpha v8 composition is 432 Stable-origin rows, 316 QR
additions, 120 strict-HA additions, 17 K3B additions, 17 K3C additions, and 21
first-round plus 42 Round-2 plus 7 `FactorialVal` plus 21 v6 and 24 v7
plus 38 v8 Bertrand additions. Its evidence partition is 432 `stable_closed`,
138 `alpha_closed`, 484 `body_checked`, and one
`pending_layered_closure`. Thus **Alpha membership does not imply checked
use**: exactly 570 of the 1,055 entries cross that boundary. Every v8 suffix row
has `checked_use=false`, a null proof tag, and null empty-context closure
metadata. Its independently replayed dependency-curried body is evidence for
that body, not empty-context admission. The current v8
ordered-enrollment root is
`a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2`;
the full edition identity is
`2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123`.
The current ordered-specification, membership, evidence, and channel-pointer
roots are
`fe49d664e5a88f6637c7790b104e9b0aa3c583e48f9a4a1405d5b098f7f61df9`,
`4471bdcf06a2d3af866850b39f394a436ad608b4c0b166c0449620e5dd3c9ee3`,
`4230c17701be2c604ea413be90c26bad41889d593dcaaeff311217b4e26367b4`,
and
`1fd2216e0448fbeb0d8da60dea3b89fca4d4f7192371fc87a8c5cd35dccf3c70`.
The sealed v7 enrollment and edition identities remain
`aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c`
and
`9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff`.
The sealed v7 ordered-specification root remains
`838c8f48f81eddcdf3e9de0f9557cee1c25eb78015513d99cfe8ab76975edc65`.
The sealed v7 membership and evidence roots remain
`e6d22473986c7e4ec1e4566f156c3dad710a4a9be2ae7b830490546da48cb703`
and
`a3709e040891b7c180c5c35876ec0e033b58ad12ce5179c3b0215ed11c1a93b6`;
the channel-pointer root is
`e868088b8abf7b98e1a3976058adfca5ed542a1d9b29c275ebd16c070cd810c3`.
The exact v7 artifact SHA-256 values are catalog
`7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4`,
metrics
`c40f18bda0ec8feb9294cf445d08b51daf868e46b3931daf55bad91413d39e0d`,
reduced graph
`85a53bd719e227a31d5cff15fc25ff66abaa82d498030f5a918a7c40271abc9e`,
and channels
`fe9c11ec8a622eb759053a42ee6acb7c2bcb1d454fe0dc5fa4b729a07ffbbd30`.
The sealed v6 parent catalog remains byte-bound by SHA-256
`c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d`.

The v8 artifact family is
`artifacts/peano-library/alpha/catalog-v8.json`,
`artifacts/peano-library/alpha/metrics-v8.json`,
`artifacts/peano-library/alpha/dependency-graph-v8.mmd`, and
`artifacts/peano-library/channels-v8.json`. Their SHA-256 values are,
respectively,
`c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370`,
`90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813`,
`ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008`,
and
`dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d`.
The binding control document is
[`RFC HA-R6-BERTRAND-CB-1`](../../research/arithmetic-library/ha-bertrand-choose-central-binomial-tranche-rfc-v1.md).

The 557-row focused QR slice omits 191 Stable theorems and 269 Alpha additions
from the strict-HA, K3B, K3C, and Bertrand tranches; its union with all Stable
rows has **748** distinct names. Likewise, the 41-node K3B map is a
deliberately curated visual lens, not a competing catalog. The authoritative
channel pointers are
`artifacts/peano-library/channels-v8.json`; it links the current Alpha v8
catalog, metrics, and graph, while the pre-existing Stable artifact remains
`artifacts/peano-library/catalog-v1.json`. The v1 channel and Alpha v1
artifacts remain sealed parents.

The {doc}`Stable theorem atlas <theorem-atlas>` is authoritative for the 432
registered theorems. The {doc}`QR proof explorer <proof-explorer>` is an Alpha
campaign slice, and the {doc}`K3B CellHistory/ListAt chapter
<cell-history-and-lookup>` is an Alpha layer with its own sealed receipt. The
{doc}`K3C validity and membership chapter <list-validity-and-membership>`
documents the additive body-checked layer and its pending closure boundary.
The {doc}`Bertrand campaign chapter <bertrand-campaign>` documents the next
additive layers, including the completed body proofs of finite Legendre
recurrence, factorial--Legendre equality, compact $H/J$ transport,
recurrence-defined Choose/CentralBinom, and the strict central lower bound.
The primorial and no-prime central upper bounds, branch integration, finite
coverage, and capstone remain open.

## Release membership and proof evidence are different axes

Every theorem should be read using two independent labels:

| Axis | Values used here | Question answered |
|---|---|---|
| release membership | `stable`, `alpha-only` | Which cumulative edition contains this row? |
| proof evidence | body checked, closed checked, closure pending | What has actually been replayed and checked? |

For example, all seventeen selected K3B roots are **Alpha-only** and **closed
checked**. Their WMI certificates are real empty-context evidence, but the
layer has not yet passed Stable promotion. A quadratic-reciprocity support row
may instead be **Alpha-only** and only **body checked**, meaning its declared
dependencies remain hypotheses in that particular receipt.
All seventeen K3C rows are in this second state: local body, liveness, and
mutation gates pass, but their repeated isolated WMI empty-context receipt is
pending. They therefore fail closed through checked use.
All twenty-one Alpha-v3 Bertrand rows, all forty-two Alpha-v4 Round-2 rows,
the seven Alpha-v5 `FactorialVal` rows, the twenty-one Alpha-v6 rows, the
twenty-four Alpha-v7 rows, and the thirty-eight Alpha-v8 rows are
in the same body-only state. They include exact valuation
multiplication, ceiling/floor-square, and quotient-budget theorems whose local
closures are useful feasibility evidence but do not make them checked-use
facts. Their dependency-curried bodies and local closures have been checked,
but they have null proof tags, no empty-context admission receipt, and fail
closed through replay.

Alpha v7 enrolled the earlier Legendre-successor and capacity-shared
`PowTotal` candidates together with the initial-segment constructors, compact
$H/J$ base window and transport, finite Legendre recurrence, and
factorial--Legendre agreement. In particular,
`prime_factorial_valuation_eq_legendre_sum` is complete as a checked theorem
body, and the three compact six-step $H/J$ transport bodies are complete.
These are body-evidence claims: none of the twenty-four rows was promoted or
made available through checked replay. Bertrand's postulate itself remains
open.

Alpha v8 adds the constructive recurrence-defined `Choose` foundation,
functionality, Pascal recurrence, symmetry and positivity; relational
`CentralBinom` existence, functionality, positivity, zero and successor laws;
the weighted vertical and factorial bridges; and the exact lower bound
`four_pow_lt_mul_central_binom`. All thirty-eight additions remain
`body_checked`, unavailable through checked replay, and unpromoted. The
primorial and no-prime central upper bounds, large-input contradiction, finite
coverage, and Bertrand endpoints remain open.

Definitions are a third kind of object. They are displayed as yellow hexagons
because they expand conservatively before parsing; they are neither theorem
premises nor additional axioms.

## Checked use in each edition

Stable remains the default checked-use registry. It contains the 432 theorems recorded in
[`catalog-v1.json`](https://github.com/nasqret/vietnam2026/blob/2037b87905817ada187e2477af22c57ff47fb512/artifacts/peano-library/catalog-v1.json).
Those rows may be imported through the ordinary library workflow.

Alpha has an explicit opt-in checked-use API. It admits only entries whose
evidence is `stable_closed` or `alpha_closed`; a `body_checked` or
`pending_layered_closure` request fails closed.

```python
from peano_lab.library.editions_v8 import edition, entry, replay

len(edition("stable").specs)          # 432
len(edition("alpha").specs)           # 1055
len(edition("alpha").checked_specs)   # 570

entry("cell_list_extensional", edition="alpha")
replay("signed_decode_nonnegative_constructor", edition="alpha")
```

The ordinary Stable API is unchanged and remains the default. Alpha replay
constructs a complete dependency certificate only for an explicitly selected
checked-use row; it does not scan arbitrary `*_candidate.py` files or infer
authority from documentation. Metadata lookup is cheap, but replay cost varies
with the transitive certificate: `cell_list_extensional`, for example, closes
to 95,253 proof nodes. Use the sealed receipts or WMI verification for such
large rows instead of treating them as laptop smoke tests.

External website deployment is separate again. A Stable repository snapshot
does not become Alpha merely because a hosted Peano Lab has not yet deployed
that commit.

## Promotion lifecycle

```text
authored and dependency-frozen
  -> Alpha enrollment with explicit evidence
  -> recursive empty-context closure and mutation checks
  -> compilation, resource, and dependency-link audit
  -> notation, Book, vault, and artifact synchronization
  -> append-only Stable promotion
  -> optional external deployment
```

A Stable promotion should therefore establish all of the following:

1. The exact statement and dependency list are frozen and dependency-closed.
2. The authored body checks, and its complete recursive certificate checks
   from the empty context with the intended intuitionistic kernel.
3. Repeated cold replay is deterministic; proof hashes and structural metrics
   are pinned in a receipt.
4. Mutation tests reject meaningful changes, and the DNE/classical profile is
   recorded rather than inferred from prose.
5. Certificate size, depth, memory, compilation time, and browser limits have
   been measured before admission.
6. Direct links have been reviewed for unnecessary dependencies. The catalog
   stores every declared direct edge; sparse review graphs may hide explicitly
   reported reachability-redundant arrows, without claiming that their proof
   hypotheses are unused or mathematically unnecessary.
7. Definitions expand hygienically to the same PA formulas, and all Book,
   explorer, catalog, artifact, and vault views agree.
8. The Stable registry is updated append-only, preserving earlier theorem
   identities and the released training prefix.

Promotion publishes a new channel version; it never edits the v1 evidence
ledger in place. In later versions, Stable need not be a prefix or subsequence
of Alpha's immutable enrollment order. The durable invariant is keyed exact
subset identity: every Stable name resolves to the same Alpha statement,
dependencies, script, and enrollment metadata. Stable retains its own
append-only, dependency-topological promotion order, while Alpha retains its
own historical enrollment order and scattered Stable-membership flags.

## Reading the graphs

The visual vocabulary is deliberately small:

| Shape and color | Meaning |
|---|---|
| green rectangle | Stable theorem |
| blue rounded rectangle | Alpha-only theorem |
| yellow hexagon | conservative display definition |
| solid arrow | direct proof dependency, prerequisite to dependent |
| dashed purple arrow | notation occurrence; never part of a proof path |

Graphs open in **direct neighborhood** mode and draw only arrows incident to
the selected node. Full-map and all-arrow modes remain opt-in. Release status,
proof receipts, and promotion are node metadata, not extra arrows.

Continue with the {doc}`Stable theorem atlas <theorem-atlas>` for the released
library, the {doc}`Alpha QR proof explorer <proof-explorer>` for the reciprocity
campaign slice, the {doc}`K3B Alpha layer <cell-history-and-lookup>` for the
finite-data representation, or the {doc}`K3C Alpha layer
<list-validity-and-membership>` for its validity, membership, and semantic
lookup interface.

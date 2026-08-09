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
rows. Alpha v4 remains sealed at 965 rows. Current Alpha v5 preserves the
entire v4 enrollment ledger exactly, then appends seven `FactorialVal` rows at
indices 965--971. The initial
Stable prefix is a historical
fact about these channels, not the permanent promotion rule.

| Surface | Exact scope | What the count means |
|---|---:|---|
| Stable catalog and theorem atlas | **432** theorems | complete registered, empty-context-checked library |
| Sealed Alpha v1 catalog | **885** theorems | immutable parent: 432 Stable plus 453 Alpha-only rows |
| Sealed Alpha v2 catalog | **902** theorems | immutable parent: 432 Stable plus 470 Alpha-only rows |
| Sealed Alpha v3 catalog | **923** theorems | immutable parent: 432 Stable plus 491 Alpha-only rows |
| Sealed Alpha v4 catalog | **965** theorems | immutable parent: 432 Stable plus 533 Alpha-only rows |
| Current Alpha v5 catalog | **972** theorems | 432 Stable plus 540 Alpha-only rows |
| Alpha checked-use subset | **570** theorems | 432 `stable_closed` plus 138 `alpha_closed` rows |
| Alpha v5 proof graph | **2,912** edges / **45** layers | exact direct dependencies for all 972 enrolled rows |
| Quadratic-reciprocity Alpha slice | **557** specifications | 241 Stable prerequisites and 316 Alpha-only specifications |
| Stable $\cup$ QR slice | **748** distinct theorem names | 432 Stable plus the 316 QR Alpha-only rows |
| K3B focused map | **41** nodes | 12 Stable prerequisites, 22 Alpha-only theorem/support nodes, and 7 conservative definitions |
| K3B cold-closure receipt | **17** selected roots | two deterministic empty-context WMI passes, all with zero DNE |
| K3C additive tranche | **17** specifications | indices 885--901, all `body_checked`, cold receipt pending |
| Bertrand first-round tranche | **21** specifications | indices 902--922, all `body_checked`, cold receipt pending |
| Bertrand Round-2 tranche | **42** specifications | indices 923--964, all `body_checked`, fail-closed |
| Bertrand `FactorialVal` tranche | **7** specifications | indices 965--971, all `body_checked`, fail-closed |

For comparison, the sealed Alpha v1 proof graph has **2,641** edges / **45** layers,
and its evidence partition was 432 `stable_closed`, 138 `alpha_closed`,
314 `body_checked`, and one `pending_layered_closure`. Its immutable machine
surfaces remain `artifacts/peano-library/channels.json` and
`artifacts/peano-library/alpha/catalog-v1.json`; Alpha v2, v3, v4, and v5 are
additive children, not in-place rewrites of either file.
The sealed Alpha v3 graph had **2,730** edges / **45** layers and 352 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v3.json`.
The sealed Alpha v4 graph had **2,891** edges / **45** layers and 394 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v4.json`.

The canonical Alpha v5 composition is 432 Stable-origin rows, 316 QR
additions, 120 strict-HA additions, 17 K3B additions, 17 K3C additions, and 21
first-round plus 42 Round-2 plus 7 `FactorialVal` Bertrand additions. Its
evidence partition is 432 `stable_closed`, 138 `alpha_closed`, 401 `body_checked`,
and one
`pending_layered_closure`. Thus **Alpha membership does not imply checked
use**: exactly 570 of the 972 entries cross that boundary. The v5
ordered-enrollment root is
`46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473`;
the full edition identity is
`bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af`.
Its ordered-specification root is
`4592f0abba7b9f592d4f94780ced57c3e7e0b935444155f76276f1fd2b4d8ae4`.
The membership and evidence roots are
`b3b71470fd6519b227e2353b818935f673a9d50dab6d59474f0f5f241ee20277`
and
`a36ce30e7f95cde8fcb8bf73413d46a0b851eb52694387ba1fcc7327a08d4abb`;
the channel-pointer root is
`fa8cc554a6aa8eeab1aa396cbfc4f8019d16fa97d91aa09daa3e9ea4839db7f4`.
The exact v5 artifact SHA-256 values are catalog
`94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892`,
metrics
`b560373c8cb4879f47e46083d5b9925cd29ebee1af4856cfc93e74017555acc2`,
reduced graph
`4e8f1ea73b3ecfd51cf80d216dfc9171dabbe12f38d9c8392185ea1c610112ab`,
and channels
`946682733744d6969e89059df9165cc2782510101d4ee43a6a861aa7570a3f31`.
The sealed v4 parent retains enrollment root
`e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31`
and edition identity
`e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5`.

The number **748** describes only Stable union the focused QR slice. That
slice omits 191 Stable theorems and 224 Alpha additions from the strict-HA,
K3B, K3C, and Bertrand tranches. Likewise, the 41-node K3B map is a deliberately curated visual
lens, not a competing catalog. The authoritative channel pointers are
`artifacts/peano-library/channels-v5.json`; it links the current Alpha v5
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
additive layers, the enrolled factorial-valuation recurrence, the pushed
finite-sum and threshold candidates, and the equality and integer-power gates
that remain open.

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
All twenty-one Alpha-v3 Bertrand rows and all forty-two Alpha-v4 Round-2 rows
are in the same body-only state. The latter include exact valuation
multiplication, ceiling/floor-square, and quotient-budget theorems whose local
closures are useful feasibility evidence but do not make them checked-use
facts. The seven Alpha-v5 `FactorialVal` rows are likewise Alpha-only
`body_checked` rows: their dependency-curried bodies and local closures have
been checked, but they have null proof tags, no empty-context admission
receipt, and fail closed through replay.

Repository presence is not enrollment. The eight threshold-base rows pushed
in `f35b8ed` and the five finite Legendre-sum rows pushed in `4df44c9` are
reviewed candidates outside Alpha v5. The relational-power bridge remains
under audit. None changes the v5 counts or checked-use boundary, and the
finite-sum interface is not yet Legendre's equality with factorial valuation.

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
from peano_lab.library.editions_v5 import edition, entry, replay

len(edition("stable").specs)          # 432
len(edition("alpha").specs)           # 972
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

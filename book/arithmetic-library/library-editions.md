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
editions. Stable v1 remains sealed at 432 rows, and Alpha v1 remains sealed at
885 rows. Current Alpha v2 preserves the entire v1 enrollment ledger exactly,
then appends the seventeen K3C rows at indices 885--901. The initial Stable
prefix is a historical fact about these channels, not the permanent promotion
rule.

| Surface | Exact scope | What the count means |
|---|---:|---|
| Stable catalog and theorem atlas | **432** theorems | complete registered, empty-context-checked library |
| Sealed Alpha v1 catalog | **885** theorems | immutable parent: 432 Stable plus 453 Alpha-only rows |
| Current Alpha v2 catalog | **902** theorems | 432 Stable plus 470 Alpha-only rows |
| Alpha checked-use subset | **570** theorems | 432 `stable_closed` plus 138 `alpha_closed` rows |
| Alpha v2 proof graph | **2,674** edges / **45** layers | exact direct dependencies for all 902 enrolled rows |
| Quadratic-reciprocity Alpha slice | **557** specifications | 241 Stable prerequisites and 316 Alpha-only specifications |
| Stable $\cup$ QR slice | **748** distinct theorem names | 432 Stable plus the 316 QR Alpha-only rows |
| K3B focused map | **41** nodes | 12 Stable prerequisites, 22 Alpha-only theorem/support nodes, and 7 conservative definitions |
| K3B cold-closure receipt | **17** selected roots | two deterministic empty-context WMI passes, all with zero DNE |
| K3C additive tranche | **17** specifications | indices 885--901, all `body_checked`, cold receipt pending |

For comparison, the sealed Alpha v1 proof graph has **2,641** edges / **45** layers,
and its evidence partition was 432 `stable_closed`, 138 `alpha_closed`,
314 `body_checked`, and one `pending_layered_closure`. Its immutable machine
surfaces remain `artifacts/peano-library/channels.json` and
`artifacts/peano-library/alpha/catalog-v1.json`; Alpha v2 is an additive child,
not an in-place rewrite of either file.

The canonical Alpha v2 composition is 432 Stable-origin rows, 316 QR
additions, 120 strict-HA additions, 17 K3B additions, and 17 K3C additions.
Its evidence partition is 432 `stable_closed`, 138 `alpha_closed`, 331 `body_checked`, and one
`pending_layered_closure`. Thus **Alpha membership does not imply checked
use**: exactly 570 of the 902 entries cross that boundary. The v2
ordered-enrollment root is
`00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe`;
the full edition identity is
`aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4`.

The number **748** describes only Stable union the focused QR slice. That
slice omits 191 Stable theorems and 154 Alpha additions from the strict-HA,
K3B, and K3C tranches. Likewise, the 41-node K3B map is a deliberately curated visual
lens, not a competing catalog. The authoritative channel pointers are
`artifacts/peano-library/channels-v2.json`; it links the current Alpha v2
catalog, metrics, and graph, while the pre-existing Stable artifact remains
`artifacts/peano-library/catalog-v1.json`. The v1 channel and Alpha v1
artifacts remain sealed parents.

The {doc}`Stable theorem atlas <theorem-atlas>` is authoritative for the 432
registered theorems. The {doc}`QR proof explorer <proof-explorer>` is an Alpha
campaign slice, and the {doc}`K3B CellHistory/ListAt chapter
<cell-history-and-lookup>` is an Alpha layer with its own sealed receipt. The
{doc}`K3C validity and membership chapter <list-validity-and-membership>`
documents the additive body-checked layer and its pending closure boundary.

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
from peano_lab.library.editions_v2 import edition, entry, replay

len(edition("stable").specs)          # 432
len(edition("alpha").specs)           # 902
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

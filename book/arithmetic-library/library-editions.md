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
rows, Alpha v6 remains sealed at 993 rows, Alpha v7 remains sealed at 1,017
rows, Alpha v8 remains sealed at 1,055 rows, Alpha v9 remains sealed at 1,076
rows, Alpha v10 remains sealed at 1,085 rows, and Alpha v11 remains sealed at
1,123 rows. Sealed Alpha v12 has 1,303 rows; v13 has 1,543, v14 has 1,556,
and v15 has 1,673. Current Alpha v16 preserves the exact v15 statement order,
membership, dependencies, and enrollment identity, then changes only the
evidence of 315 genuinely closed quadratic-reciprocity theorems. Its final
root and every prerequisite have real independently checked certificates,
whereas all 788 unrelated body-only rows remain unavailable. Stable is still
the unchanged 432-theorem default; the initial Stable prefix is a historical
fact about these channels, not the permanent promotion rule.

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
| Sealed Alpha v8 catalog | **1,055** theorems | immutable parent: 432 Stable plus 623 Alpha-only rows |
| Sealed Alpha v9 catalog | **1,076** theorems | immutable parent: 432 Stable plus 644 Alpha-only rows |
| Sealed Alpha v10 catalog | **1,085** theorems | immutable parent: 432 Stable plus 653 Alpha-only rows |
| Sealed Alpha v11 catalog | **1,123** theorems | immutable parent: 432 Stable plus 691 Alpha-only rows |
| Sealed Alpha v12 catalog | **1,303** theorems | 432 Stable plus 871 Alpha-only rows |
| Sealed Alpha v13 catalog | **1,543** theorems | Lagrange four-square and multidigit Lucas campaign |
| Sealed Alpha v14 catalog | **1,556** theorems | Kummer carry theorem and carry-free corollary |
| Sealed Alpha v15 catalog | **1,673** theorems | supplementary laws and the complete two-square classification |
| Current Alpha v16 catalog | **1,673** theorems | unchanged enrollment; exactly 315 closed QR evidence promotions |
| Historical Alpha v12--v15 checked-use subset | **570** theorems | 432 `stable_closed` plus 138 `alpha_closed` rows |
| Current Alpha v16 checked-use subset | **885** theorems | 432 `stable_closed` plus 453 `alpha_closed` rows |
| Historical Alpha v12 proof graph | **4,302** edges / **45** layers | exact direct dependencies for all 1,303 enrolled rows |
| Current Alpha v16 proof graph | **5,615** edges / **53** layers | unchanged exact direct dependencies for all 1,673 enrolled rows |
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
| Bertrand Alpha-v9 tranche | **21** specifications | indices 1055--1075 in exact 10+11 microbatches, all `body_checked`, fail-closed |
| Bertrand Alpha-v10 tranche | **9** specifications | indices 1076--1084 in exact 1+8 dependency order, all `body_checked`, fail-closed |
| Bertrand Alpha-v11 tranche | **38** specifications | indices 1085--1122 in exact 20+18 microbatches, all `body_checked`, fail-closed |
| Bertrand Alpha-v12 tranche | **180** specifications | indices 1123--1302 in nine exact twenty-row microbatches, all `body_checked`, fail-closed |

For comparison, the sealed Alpha v1 proof graph has **2,641** edges / **45** layers,
and its evidence partition was 432 `stable_closed`, 138 `alpha_closed`,
314 `body_checked`, and one `pending_layered_closure`. Its immutable machine
surfaces remain `artifacts/peano-library/channels.json` and
`artifacts/peano-library/alpha/catalog-v1.json`; Alpha v2 through v12 are
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
The sealed Alpha v8 graph had **3,224** edges / **45** layers and 484 `body_checked`
rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v8.json`.
The sealed Alpha v9 graph had **3,276** edges / **45** layers and
505 `body_checked` rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v9.json`.
The sealed Alpha v10 graph had **3,306** edges / **45** layers and
514 `body_checked` rows; its immutable channel pointer remains
`artifacts/peano-library/channels-v10.json`.
The sealed Alpha v11 graph had **3,482** edges / **45** layers and
552 `body_checked` rows. Its enrollment, edition, specification, membership,
evidence, channel-pointer, suffix-depth, and body-receipt roots remain
`c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`,
`46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`,
`4a1f4302b0a4ede3bf5123ec021b4f2f5f98c2a7e22eadc6f13a446422ad9450`,
`2f0be30e7de93bcf89235700c419f46656cb638be85ca153154684845e8dabdb`,
`b82b567e59cabeda6f90fdfedaceb628ca2e7c4b7423be643b8f22865e7599bd`,
`ecce457947650ae7ddf2a638d8b1f2c8757daea6a95ea9c927ebaef3995d4ccd`,
`cf5d550d5a3aa4af1debf9268eca578c30ca408058dcdeb35892bc705287214e`,
and
`6c314d36cd7bb1e6cb5b213fec9bf9e04ab118e84121830b00c885ede2abac2a`.

The sealed historical Alpha v12 composition is 432 Stable-origin rows, 316 QR
additions, 120 strict-HA additions, 17 K3B additions, 17 K3C additions, and 21
first-round plus 42 Round-2 plus 7 `FactorialVal` plus 21 v6 and 24 v7
plus 38 v8, 21 v9, 9 v10, 38 v11, and 180 v12 Bertrand additions. Its evidence
partition is 432 `stable_closed`, 138 `alpha_closed`, 732 `body_checked`, and one
`pending_layered_closure`. Thus **Alpha membership does not imply checked
use**: exactly 570 of the 1,303 historical entries cross that boundary. Every v12 suffix row
has `checked_use=false`, a null proof tag, and null empty-context closure
metadata. Its independently replayed dependency-curried body is evidence for
that body, not empty-context admission. The historical v12
ordered-enrollment root is
`f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b`;
the full edition identity is
`bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061`.
The historical v12 ordered-specification, membership, evidence, and channel-pointer
roots are, respectively,
`362da94c3c5e788f296f315b86b5d63534c1567ce00911dbb27227a66ab50e28`,
`726c6134461dace943f909a0073ca0a6cae95a54ff306f8aeefeb3d9a5151926`,
`de8a6a57b828c2b3893c6fb31f2611d5180f8de4d1002a21a681739616b761b5`,
and
`7ad0c942a2239532696f5d99ee1dc985e13302cf73b4637497b879871d05752c`.
The suffix-depth and fresh 180-body receipt roots are
`ee9494f8dfb9e4070a2ce3d2d740b312d147948dcd296ac0da7ed059c9944e50`
and
`df0e5cb8402483360f8381c76c7ce6ed6c70245df45556107c40652d00beb0da`.
The sealed v10 enrollment, edition, specification, membership, evidence, and
channel-pointer roots remain
`c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f`,
`1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d`,
`6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46`,
`01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013`,
`a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a`,
and
`f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e`.
Its suffix-depth and nine-body receipt roots remain
`446f6c9d07c3f9e22fa0fbb41a46c95d27804a088d708b13aea0ddd7159c45dd`
and
`fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c`.
The sealed v9 enrollment, specification, edition, membership, evidence, and
channel-pointer roots remain
`fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f`,
`762d1310c41ed92da066701cf7529551324b09f7b501c5a29c530f443afeb998`,
`b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80`,
`4c87c40b5a260d67b5582447cfabb7e3ce62e80303aa4f4d33b1b952995ec356`,
`108593843459a69d81c333305a50b5368294c3c722437f425b92c942391fe9be`,
and
`edfb0eacecbd9419b1b303098915e28e45643379b65ab7d807ffcd4d7bd4b3e7`.
Its suffix-depth and fresh twenty-one-body receipt roots remain
`61f33ba9e49219ff4a199d082722d9582ac6d87f825851173ac7fdb6931bb52d`
and
`1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab`.
The sealed v8 enrollment and edition identities remain
`a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2`
and
`2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123`.
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
The v8 binding control document is
[`RFC HA-R6-BERTRAND-CB-1`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-choose-central-binomial-tranche-rfc-v1.md).

The v9 artifact family is
`artifacts/peano-library/alpha/catalog-v9.json`,
`artifacts/peano-library/alpha/metrics-v9.json`,
`artifacts/peano-library/alpha/dependency-graph-v9.mmd`, and
`artifacts/peano-library/channels-v9.json`. Their SHA-256 values are,
respectively,
`74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda`,
`7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65`,
`03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9`,
and
`77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34`.
Its ten foundation rows and eleven membership rows bind, respectively, to the
[`Primorial foundation RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-foundation-tranche-rfc-v1.md)
and
[`Primorial membership RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-membership-tranche-rfc-v1.md).

The v10 artifact family is
`artifacts/peano-library/alpha/catalog-v10.json`,
`artifacts/peano-library/alpha/metrics-v10.json`,
`artifacts/peano-library/alpha/dependency-graph-v10.mmd`, and
`artifacts/peano-library/channels-v10.json`. Their SHA-256 values are,
respectively,
`46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3`,
`63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de`,
`fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76`,
and
`644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2`.
Its exact 1+8 append binds to the
[`Primorial interval-split RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-interval-split-tranche-rfc-v1.md).

The v11 artifact family is
`artifacts/peano-library/alpha/catalog-v11.json`,
`artifacts/peano-library/alpha/metrics-v11.json`,
`artifacts/peano-library/alpha/dependency-graph-v11.mmd`, and
`artifacts/peano-library/channels-v11.json`. Their SHA-256 values are,
respectively,
`d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c`,
`92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300`,
`c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1`,
and
`039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f`.
Its five source blocks bind to the duplicate-free, Primorial/Choose interval,
central-upper, Primorial-four-power, and central-prime-support RFCs.

The v12 artifact family is
`artifacts/peano-library/alpha/catalog-v12.json`,
`artifacts/peano-library/alpha/metrics-v12.json`,
`artifacts/peano-library/alpha/dependency-graph-v12.mmd`, and
`artifacts/peano-library/channels-v12.json`. Their SHA-256 values are,
respectively,
`825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109`,
`64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4`,
`583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8`,
and
`0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982`.
Its 180-row append binds the B6 release RFC plus the reviewed B5, B7, B8,
BP01, and BP02 tranche RFCs. The full dependency-closed candidate proof ends
in `bertrand_closed_upper` and `bertrand_strict`.

The 557-row focused QR slice omits 191 Stable theorems; its union with all
Stable rows has **748** distinct names, leaving 925 other current Alpha v16
entries outside that union. Likewise, the 41-node K3B map is a deliberately
curated visual lens, not a competing catalog. The current authoritative
channel pointer is `artifacts/peano-library/channels-v16.json`; it links the
immutable Alpha v16 catalog, metrics, and graph, while the pre-existing Stable
artifact remains `artifacts/peano-library/catalog-v1.json`. The historical
`artifacts/peano-library/channels-v12.json` pointer and every Alpha v1--v15
artifact remain sealed parents. The unchanged v16 enrollment identity is
`44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175`;
its promoted-evidence identity is
`3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10`.
The current evidence ledger is 432 `stable_closed`, 453 `alpha_closed`, 788
`body_checked`, and zero pending rows; exactly 885 permit checked use.

The {doc}`Stable theorem atlas <theorem-atlas>` is authoritative for the 432
registered theorems. The {doc}`QR proof explorer <proof-explorer>` is an Alpha
campaign slice, and the {doc}`K3B CellHistory/ListAt chapter
<cell-history-and-lookup>` is an Alpha layer with its own sealed receipt. The
{doc}`K3C validity and membership chapter <list-validity-and-membership>`
documents the additive body-checked layer and its pending closure boundary.
The {doc}`Bertrand campaign chapter <bertrand-campaign>` documents the
additive layers, including the completed body proofs of finite Legendre
recurrence, factorial--Legendre equality, compact $H/J$ transport,
recurrence-defined Choose/CentralBinom, the strict central lower bound, and
the Primorial foundation, membership, monotonicity, exact interval splitting,
duplicate-free product comparison, `primorial_le_four_pow`, the no-prime
central upper bound, branch integration, finite coverage, and both Bertrand
endpoints.

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
twenty-four Alpha-v7 rows, the thirty-eight Alpha-v8 rows, the twenty-one
Alpha-v9 rows, the nine Alpha-v10 rows, the thirty-eight Alpha-v11 rows, and
the 180 Alpha-v12 rows are
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

Alpha v9 adds the conservative inclusive `Primorial` relation and its
existence, functionality, zero, successor-decomposition, and positivity laws;
then it proves the exact prime-divisibility membership equivalence together
with successor and general divisibility, positive quotients, and weak numeric
monotonicity. All twenty-one additions remain `body_checked`, unavailable
through checked replay, and unpromoted. Filtered interval splitting,
duplicate-free external prime-product comparison, `primorial_le_four_pow`,
and every downstream Bertrand gate remain open.

Alpha v10 pins the reviewed generic Product prefix/suffix split, then adds an
offset selector-product relation with totality and functionality, entry
transport and shift, prefix restriction, and an exact decomposition of
`Primorial(a+l)` into a prefix value times the interval value. All nine
additions remain `body_checked`, unavailable through checked replay, and
unpromoted. Duplicate-free external-product comparison,
`primorial_le_four_pow`, and every downstream Bertrand gate remain open.

Alpha v11 enrolls the complete dependency-closed post-v10 chain: the
duplicate-free filtered-product comparison, Primorial interval divisibility
and Choose bounds, cap-safe central-binomial upper laws, the public
`primorial_le_four_pow` theorem, and the first central prime-divisor range and
valuation-support rows for B5. All thirty-eight additions remain
`body_checked`, unavailable through checked replay, and unpromoted. B4 is now
closed at candidate/body-evidence level; the five-range no-prime central upper
bound, B7 contradiction, finite coverage, and final endpoints remain open.

Alpha v12 enrolls the complete dependency-closed post-v11 proof. Its first
forty-three rows add the reviewed B6 base, growth, main inequality, and finite
product-order prerequisites. Its remaining 137 rows complete the five-range
central upper bound, B7 contradiction, finite certificate covering, and the
public `bertrand_closed_upper` and `bertrand_strict` endpoints. All 180
additions remain `body_checked`, unavailable through checked replay, and
unpromoted. The mathematical proof is complete; checked-use and Stable
promotion remain subsequent release operations.

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
from peano_lab.library.editions_v16 import edition, entry, replay

len(edition("stable").specs)          # 432
len(edition("alpha").specs)           # 1673
len(edition("alpha").checked_specs)   # 885

entry("cell_list_extensional", edition="alpha")
replay("signed_decode_nonnegative_constructor", edition="alpha")
entry("quadratic_reciprocity_combined", edition="alpha")  # alpha_closed
```

The ordinary Stable API is unchanged and remains the default. Alpha replay
constructs a complete dependency certificate only for an explicitly selected
checked-use row; it does not scan arbitrary `*_candidate.py` files or infer
authority from documentation. Metadata lookup is cheap, but replay cost varies
with the transitive certificate: `cell_list_extensional`, for example, closes
to 95,253 proof nodes. Use the sealed receipts or WMI verification for such
large rows instead of treating them as laptop smoke tests.

The browser and native shell expose the same explicit boundary through
`pa lib alpha`, `pa lib alpha <name>`, `pa lib alpha check <name>`, and
`pa lean alpha <name>`. Evidence inspection never loads the proof bundle;
checked replay and completed Lean export require the actual independently
checked closed certificate. The ordinary `pa lib` and live `use` operations
continue to use the unchanged Stable/public authority.

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

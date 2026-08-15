---
title: Foundational arithmetic library — Map of Content
tags: [moc, peano-arithmetic, number-theory, library]
---

> The executable and planned dependency graph from elementary equality through
> divisibility, modular arithmetic, primes, and unique factorization.

## Current library editions — Alpha v10, 2026-08-15

This status supersedes, without erasing, the dated checkpoint language below.
**Stable** is the unchanged official checked edition: 432 theorems, 1,185
declared direct edges, and 22 layers. Sealed **Alpha v1** remains 885 rows and
sealed **Alpha v2** remains 902 rows, and sealed **Alpha v3** remains 923
rows. Sealed **Alpha v4** remains 965 rows, sealed **Alpha v5** remains 972
rows, sealed **Alpha v6** remains 993 rows, sealed **Alpha v7** remains 1,017
rows, sealed **Alpha v8** remains 1,055 rows, and sealed **Alpha v9** remains
1,076 rows. Current additive **Alpha v10** preserves that exact v9 ledger and
appends nine Bertrand rows at indices 1076--1084 in exact 1+8 dependency
order: 1,085 theorems, 3,306 direct edges, and 45 layers, comprising Stable
plus 653 Alpha-only rows.

Membership and evidence are independent. Alpha v10 contains 432
`stable_closed`, 138 `alpha_closed`, 514 `body_checked`, and one
`pending_layered_closure` row. Only 570 closed rows are available for checked
use; the other 515 still need whole-library empty-context closure. The current
runtime surface is `peano_lab.library.editions_v10` (`edition`, `entry`,
`replay`), with Stable as the default and body-only/pending Alpha replay
rejected.

The current artifact index is `artifacts/peano-library/channels-v10.json`; it
links Alpha v10's catalog, metrics, and graph while the Stable snapshot stays
at `artifacts/peano-library/catalog-v1.json`. The v1 channel and Alpha v1
artifacts remain sealed parents. The graph's
reachability reduction is for structural review and display, not a claim of
proof-semantic minimality. Cold closure of the 515 body-only or
closure-pending Alpha rows and any Stable promotion are pending. Older
descriptions of reviewed rows as private or unregistered record their
historical Stable status; enrolled rows are now Alpha-only unless separately
promoted.

Alpha v10's enrollment, specification, edition, membership, evidence, and
channel-pointer roots are
`c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f`,
`6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46`,
`1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d`,
`01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013`,
`a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a`,
and
`f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e`.
The sealed v8 specification, membership, evidence, and channel-pointer roots
remain
`fe49d664e5a88f6637c7790b104e9b0aa3c583e48f9a4a1405d5b098f7f61df9`,
`4471bdcf06a2d3af866850b39f394a436ad608b4c0b166c0449620e5dd3c9ee3`,
`4230c17701be2c604ea413be90c26bad41889d593dcaaeff311217b4e26367b4`,
and
`1fd2216e0448fbeb0d8da60dea3b89fca4d4f7192371fc87a8c5cd35dccf3c70`.

Alpha-v8 artifact hashes are catalog
`c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370`,
metrics
`90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813`,
graph
`ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008`,
and channels
`dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d`.
Alpha-v9 artifact hashes are catalog
`74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda`,
metrics
`7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65`,
graph
`03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9`,
and channels
`77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34`.
Alpha-v10 artifact hashes are catalog
`46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3`,
metrics
`63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de`,
graph
`fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76`,
and channels
`644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2`.
The 515 missing closures are required for a whole-Alpha-v10 promotion, not
for an unrelated smaller dependency-closed batch; every proposed batch
receives its own isolated promotion receipt.

The current Stable prefix is specific to channel v1. Later promotion must keep
Alpha enrollment order and origin/provenance immutable, publish a new channel
version, and treat Stable as a keyed exact subset with its own append-only,
dependency-topological release order.

The current runtime contains 432 checked entries: 23 legacy, 212 foundation,
12 mod-five, 137 quadratic-residue, and 48 strict-HA theorems. The latest 23
public M5 rows are the exact dependency closure of the all-modulus
`generalized_binary_crt_solvable_iff`, the zero/nonzero
`generalized_binary_crt_canonical_boundary`, and the raw-input
`generalized_binary_crt_total_decision`. They follow the 16 public K4 rows and
occupy runtime indices 409--431. Six support/convenience rows remain private.
The factorization tranche is fully synchronized. The exact native sorted
Gödel-β endpoints check
from the empty context: existence at 43,973 nodes/depth 98, canonical extensional
uniqueness at 29,789/depth 82, and combined
[[fundamental-theorem-of-arithmetic|FTA]] at 73,767 nodes/depth 99 with 2,184
self-contained Cuts.

The synchronized research catalog has 433 entries: 23 `checked_existing`, 409
`checked_m20`, and one `blocked_by_language` conventional
integer-coefficient Bézout interface.

The exact FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes the 500,000-occurrence/100,000-object/depth-256 live/use gate with
PA1–PA6 and induction only and no DNE. Runtime integration is complete. No
primitive list type was added, and uniqueness compares decoded entries rather
than raw β codes. The separate Lean companion checks the conventional list
theorem without supplying Peano authority.

[[constructive-prime-unboundedness|Prime unboundedness]] is checked separately
at 4,595 nodes/depth 82 with 146 Cuts and certificate SHA-256
`8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
It uses PA1–PA6 only, contains no DNE, and passes dependency, PA, hypothesis,
and live-use audits.

The generated 432-theorem snapshot has 1,982,360 structural nodes, 468,010
proof objects, 57,692 structural Cut occurrences, 373 Cut-bearing
certificates, 1,185 dependency edges, and ordered root
`4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
The synchronized vault has 432 theorem notes, 531 total notes, and 5,377
links. The interactive atlas has 432 theorem cards and 1,185 dependency
edges.

The preceding M5 admission gate passed 30 structural and 220 proof/admission
tests, and all 25 browser/deployment contracts passed. After adding the five
private K3 pair/cell modules, the regenerated 185-source local browser app is
sealed as `a-0d9a06f601cf` (`BUILD=2026-08-04k`); no deployment is claimed.

The warning-free 47-source Book rebuild passes 26 source/explorer tests and
integrity over 2,325 HTML pages. Its byte-identical source/built explorer trees
contain 2,285 files; the 2,493-file HTML tree has SHA-256
`d9eddd01a0dcc228ceb17b75c8595f743c7e2b6bdcb1ba44e9c260e98b33f558`.

The strict-HA campaign separately records 95 public references, 121 private
closed candidates, and 169 exact receipts across 27 candidate modules and 36
focused test paths. Strict K3 now has 96 rows across 21 modules: 74 signed rows
and a 22-row `HA-K3-PAIR-1` API proving literal doubled-Cantor constructors,
shell bounds and separation, pair/cell component functionality, the
nil/constructed-cell boundary, and strict head/tail descent without division,
remainder, beta coding, CRT, classical logic, or DNE. These candidates are not
public. Valid-code decision, uniform computation histories, lists, and finite
maps remain open.

The post-K4/M3
[`HA-K3B-CELLHISTORY-1`](../../research/arithmetic-library/ha-cell-history-rfc-v1.md)
checkpoint now freezes reverse `CellHistory` and existential `CellListLen`
definitions. WMI job `219203` closed all eight first-ten theorem rows twice
from the empty context. Their exact
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` receipts are
`cell_history_nil = (155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)`,
`cell_history_extend = (29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)`,
`cell_history_succ_elim = (1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)`,
`cell_list_zero_iff_nil = (1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)`,
`cell_list_succ_iff_cell = (30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)`,
`cell_list_length_functional = (34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)`,
`cell_list_length_le_code = (31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)`, and
`cell_list_length_total = (29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)`.
All have zero DNE and remain private, unregistered, unadmitted
`closed_checked_candidate` evidence. The [report](../../artifacts/peano-library/ha-k3b-cell-history-closure-219203.json)
has SHA-256
`6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`;
the job completed `0:0` on `c3n1` in `00:04:46`, `MaxRSS=82428K`. Gates
G1--G6 and G7 quarantine/closure pass; public admission remains open. Strict
K3 and the unchanged campaign JSON remain exactly 96 rows/21 modules and 95
public references/121 private candidates/169 receipts. The separate light
gate is `make ha-k3b-cell-history-check`.

The follow-on
[`HA-K3B-LISTAT-1`](../../research/arithmetic-library/ha-cell-list-lookup-rfc-v1.md)
has a frozen surface, private body checks, and a full private cold seal. It
indexes from the outer head using
`j + S i = l`, with exact witnesses `l b c j t u`. Its hygienic expansion is
3,331 characters, 54 formula constructors, and 210 PA AST nodes, SHA-256
`b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce`;
seven focused tests pass. The first support row,
`cell_history_extend_preserves_prefix`, has a checked dependency-curried body
receipt `(5,99,139,37,139,138,0)` plus four focused audits. WMI job `219209`
closed it twice at
`(29369,81,4668,4896,229,241,7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498)`;
the [report](../../artifacts/peano-library/ha-k3b-listat-prefix-closure-219209.json)
has SHA-256
`0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560`.
It remains private and unadmitted, and public/campaign counts remain
unchanged.

The private rung `list_at_domain` is dependency-free and projects the
hidden history length plus native strict bound. Its statement receipt is
`(5903,065291362205b70ef41fff597d1d8762bff06ce7d3a5bead5dbcd8b97ea8a240)`;
its Cut-free/DNE-free certificate receipt is `(0,19,39,23,39,38,0)`.

The private outer-head equation `list_at_head_iff` has expanded statement
receipt
`(12530,9f0b3e7496f79b7cc6f4833edc14431dd614081b6f02b2d384aa80c521e2f8ed)`
and dependency-curried body receipt `(4,119,265,36,255,264,10)`. Its exact
direct dependencies are `cell_history_succ_elim`,
`cell_history_extend_preserves_prefix`, `beta_at_unique`, and `le_refl`.
The proof uses beta uniqueness at both endpoints of the selected final edge,
so it does not depend on `cell_tail_functional`. Job `219217` subsequently
cold-closed the row twice; registration, admission, and a public theorem
remain absent.

The private successor equation `list_at_succ_iff` has statement receipt
`(14716,004ef041acbcfbaaeda594f5f47fbea75ac6f8df87ca8bcf49774cfcbc3a978c)`
and dependency-curried body receipt `(3,124,198,38,196,197,2)`. Its direct
dependencies are exactly `cell_history_succ_elim`,
`cell_history_extend_preserves_prefix`, and `add_comm`. The same-history route
removes the provisional dependency on `list_at_head_iff` and PA2; reverse
extension preserves entries at both `j` and `S j`. Job `219217` subsequently
cold-closed the row twice; registration, admission, and a public theorem
remain absent.

The private external-bound row has statement receipt
`(7481,a86efefaf31c9bfce0cd146f6aab932f22962b688fdc7f6bc4dd0beeb40bc9f8)`
and body receipt `(2,23,28,17,28,27,0)`, depending exactly on
`list_at_domain` and `cell_list_length_functional`. The private in-range
existence row has statement receipt
`(6883,aeb4f15d9a96492b096f869e9361db6a31bce9a59041b1dd9f87fe221df2278c)`
and body receipt `(1,45,60,26,60,59,0)`, depending only on `add_comm`.
It converts `j+S i=l` to the history edge bound `i+S j=l` and extracts the
head constructively. Job `219217` cold-closed both T06 and T07 twice;
registration, admission, and a public theorem remain absent.

The private functionality row has statement receipt
`(8895,1eba38bb47901319d41e681ed77f218b437e4d2ff1d55f519fff82e7dc8f2361)`
and body receipt `(3,95,119,40,119,118,0)`, depending exactly on
`list_at_head_iff`, `list_at_succ_iff`, and `cell_functional`. Its generalized
induction uses the head and tail components of joint cell functionality.

The private history-independence row has statement receipt
`(7581,d0a1ac158e6e0552a8e762b69b602da0157183c832ec0cf4c270586dffcc914d)`
and body receipt `(2,92,171,38,171,170,0)`, depending exactly on
`list_at_functional` and `add_comm`. It reuses the same history edge and
compares two client lookups; no T07, beta-uniqueness theorem, or raw-code
equality is required. Both T08 and T09 have zero DNE and were cold-closed
twice by job `219217`; registration, admission, and a public theorem remain
absent.

The private extensionality row has statement receipt
`(15451,7033fcdf4c96a866e9d9e0b8381efbbd7b48ab060bcc4adad695ead30ff19831)`,
PA AST receipt `(707 total nodes,192 formula nodes)`, and body receipt
`(4,152,386,50,369,385,17)`. Its exact direct dependencies are
`cell_list_zero_iff_nil`, `cell_list_succ_iff_cell`, `list_at_head_iff`, and
`list_at_succ_iff`. Length induction compares outer heads, lifts pointwise
bounds to successor indices, recursively identifies tails, and normalizes
exact D06 with two head and four tail rewrites. It has zero DNE.

All ten ladder deliverables now have checked surface/body evidence (the first
is the frozen definition surface; T02--T10 are theorem bodies). WMI job
`219217` cold-closed the complete 17-target history/lookup stack twice from
the empty context with deterministic receipts and zero DNE throughout. Exact
new receipts in tuple order
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` are
`T03=(39,23,39,38,0,0,09c7d6d2bb9d7cd09597285eae31355cf76b8bc54d7c370f8c9507ca0377a701)`,
`T04=(32025,83,4982,5225,244,248,52bb6c215c7123e58374d23935490c71eccd3a8704de193612dacb57dd33cba7)`,
`T05=(30885,83,4923,5157,235,247,908364a06285830d2cc6b53919b4399203b12d08c89b9bb98de3cdd4efa5b8fa)`,
`T06=(34799,87,5767,6043,277,301,7c49ab5ac74468bf1537d510be4d0837bc97d2432727a3c25f00c80026a38663)`,
`T07=(133,26,127,132,6,3,6778f7b507370cb1bcd95d2bd90b0fbaea317f5ac262565152dc5eabf759698c)`,
`T08=(65579,85,5851,6140,290,296,00fc80f2b18c79f8e45a41682651c32c0fbe8b34bc39c8ca2186067c184d0a4a)`,
`T09=(65823,86,6022,6312,291,298,8868aaef643ffe84c4b5fb885d2f16c7b4872f071ce5de92149369d60c3dc20b)`, and
`T10=(95253,87,5888,6162,275,266,8558cf1c4c39c0d0d8b363e7304a6c5732cee0593548a4137d1407de58f479ec)`.
The authoritative 10,550-byte
[`report`](../../artifacts/peano-library/ha-k3b-listat-full-closure-219217.json)
has SHA-256
`c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8`.
Job `219217` completed `0:0` in `00:15:25`, `MaxRSS=54,496 KiB`, from clean
commit `cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e` and payload SHA-256
`78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835`.
At this dated checkpoint all 17 targets were private and unregistered. They
are now the K3B-origin `alpha_closed` rows in Alpha v1 and v2; they remain
outside Stable.

## K3C validity, membership, and semantic lookup

[`HA-K3C-CELLLIST-1`](../../research/arithmetic-library/ha-cell-list-validity-membership-rfc-v1.md)
adds `CellListValid(z) := exists l. CellListLen(z,l)` and
`ListMember(z,a) := exists i. ListAt(z,i,a)` as conservative notation. Its
seventeen theorem rows provide validity constructors and elimination,
head/tail membership equations, pointwise membership transport, unique
in-range lookup, lookup-based code equality, and unique outer-cell
decomposition. Read the linked Book chapter
[`K3C Alpha: valid lists, membership, and semantic lookup`](../../book/arithmetic-library/list-validity-and-membership.md).

The rows occupy Alpha v2 indices 885--901 and have `body_checked` evidence.
Their expanded statements, dependency-curried proofs, dependency-removal
tests, and false-conclusion mutations pass locally. Checked use stays 570:
the K3C rows fail closed until a repeated isolated WMI empty-context receipt
is recorded. Stable remains 432 and Alpha v1 remains 885.

## Bertrand's postulate campaign

[`HA-BERTRAND-1`](../../research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md)
freezes the constructive endpoint

\[
\forall n\ne 0\;\exists p\;\bigl(\operatorname{Prime}(p)\land n<p\land
p\le 2n\bigr)
\]

and an integer-only Erdős route through bounded prime-interval search,
prime-power valuations, binomial coefficients, prime products, and explicit
power inequalities. The navigable status page is
[`Bertrand's postulate campaign`](../../book/arithmetic-library/bertrand-campaign.md).

Current Alpha v10 preserves the exact 1,076-row Alpha v9 ledger and appends
nine Bertrand specifications at indices 1076--1084 in exact 1+8 order. The
first pins the reviewed Product prefix/suffix split; the remaining eight add
offset-Primorial interval construction and exact splitting. Together the 183
enrolled campaign rows cover the
earlier order, valuation, finite-sum, factorial, $H/J$, and central-binomial
layers plus the Primorial foundation, membership, and interval-split layers.
Every dependency-curried body checks, but all 183 remain `body_checked`;
checked use is still 570 and Stable is still 432. The append is bound by the
[`interval-split RFC`](../../research/arithmetic-library/ha-bertrand-primorial-interval-split-tranche-rfc-v1.md).

The finite Legendre recurrence,
`prime_factorial_valuation_eq_legendre_sum`, compact $H/J$ transport,
recurrence-defined Choose/CentralBinom API, strict central lower bound, and
Primorial foundation/membership/monotonicity and interval-split laws are
therefore complete body evidence, not empty-context admission or promotion.
Duplicate-free product comparison, `primorial_le_four_pow`, the
no-prime central upper bound, large-input contradiction, finite coverage, and
Bertrand's postulate itself are **not yet proved**. Heavy local gates run
serially, with each of the two new focused suites or each
mutation group in a fresh Python process and no concurrent proof worker.

## Design and trust

- [[quadratic-reciprocity-moc]]
- [[strict-ha-number-theory-campaign]]
- [[foundational-arithmetic-library]]
- [[lemma-dependency-dag]]
- [[arithmetic-library-provenance]]
- [[theorem-ladder]]
- [[trusted-kernel]]
- [[conservative-library-curation]]
- [[proof-certificate]]
- [[self-contained-proof-sharing]]
- [[layered-cut-bundle]]
- [[closed-proof-dag]]
- [[library-epoch]]
- [[sealed-theorem-benchmark]]

## Mathematical concepts

- [[arithmetic-congruence]]
- [[divisibility]]
- [[quotient-and-remainder]]
- [[gcd-and-coprimality]]
- [[prime-number]]
- [[euclids-lemma]]
- [[fundamental-theorem-of-arithmetic]]
- [[godel-beta-sequence]]

## Checked equality and additive nodes

- [[zero_add]] · [[add_succ_left]] · [[add_comm]] · [[add_assoc]]
- [[eq_symm]] · [[eq_trans]] · [[succ_congr]] · [[add_congr]]
- [[add_right_cancel]] · [[add_left_cancel]] · [[add_eq_zero_right]] · [[add_eq_zero_left]]
- [[add_eq_zero_components]] · [[add_le_add_left]] · [[add_le_add_right]] · [[add_le_cancel_right]]
- [[no_succ_add_fixed]] · [[drop_add_prefix_from_fixed]]
- [[add_permute_outer]]

## Checked multiplication nodes

- [[mul_zero_left]] · [[mul_succ_left]] · [[mul_comm]] · [[mul_add]]
- [[mul_assoc]] · [[one_mul]] · [[mul_one]] · [[add_mul]] · [[mul_congr]]
- [[mul_eq_zero]] · [[mul_ne_zero]] · [[two_large_factors_impossible]]
- [[mul_eq_one_components]]
- [[mul_left_cancel_nonzero]] · [[mul_right_cancel_nonzero]]
- [[mul_le_mul_left]] · [[mul_le_mul_right]] · [[mul_lt_mul_succ_left_nonzero]]

## Checked order nodes

- [[succ_ne_zero]] · [[succ_injective]]
- [[le_refl]] · [[le_trans]] · [[antisymm_from_witnesses]]
- [[le_antisymm]] · [[le_total]] · [[zero_le]] · [[le_succ_self]] · [[le_zero]]
- [[le_eq_or_lt]] · [[lt_trichotomy]] · [[lt_trans]] · [[lt_not_le]] · [[le_not_lt]]

## Checked divisibility nodes

- [[multiple_zero]] · [[one_multiple]] · [[multiple_refl]]
- [[multiple_add]] · [[multiple_mul_right]] · [[multiple_mul_left]]
- [[right_factor_divides_product]]
- [[multiple_trans]] · [[multiple_antisymm]]
- [[divisor_le_nonzero]] · [[divisor_one]]
- [[factor_difference]] · [[divides_remainder]] · [[divides_linear_step]]
- [[not_multiple_pointwise]] · [[not_multiple_from_pointwise]]

## Checked gcd and coprimality API

- [[is_gcd_symm]] · [[is_gcd_dvd_left]] · [[is_gcd_dvd_right]]
- [[is_gcd_greatest]] · [[is_gcd_of_dvd]] · [[is_gcd_unique]]
- [[is_gcd_zero_right]] · [[is_gcd_euclid_forward]] · [[is_gcd_euclid_backward]]
- [[gcd_exists_up_to]] · [[gcd_exists_relational]]
- [[coprime_symm]] · [[coprime_one_left]] · [[coprime_one_right]]
- [[coprime_to_is_gcd_one]] · [[is_gcd_one_to_coprime]]

## Checked balanced Bézout and Gauss nodes

- [[balanced_bezout_euclid_step]]
- [[gcd_balanced_bezout_exists_up_to]] · [[gcd_balanced_bezout_exists]]
- [[balanced_combination_scale_right]] · [[common_divisor_divides_balanced_result]]
- [[coprime_balanced_bezout]] · [[gauss_coprime_cancel]]
- [[bezout_mod_left]] · [[bezout_mod_right]]

## Checked quotient-and-remainder algebra

- [[division_remainder_succ]] · [[division_remainder_exists]] · [[division_remainder_unique]]
- [[remainder_bound_step]] · [[division_block_upper]] · [[positive_quotient_gap_impossible]]
- [[zero_remainder_implies_multiple]] · [[multiple_has_zero_remainder]]
- [[add_residue]] · [[add_residue_lift]]
- [[square_decomp]] · [[square_residue_lift]] · [[square_residue_witness]]

## Checked congruence, binary CRT, and β decoding

- [[mod_eq_refl]] · [[mod_eq_symm]] · [[mod_eq_trans]] · [[mod_eq_add]]
- [[mod_eq_mul_right]] · [[mod_eq_mul_left]] · [[mod_eq_mul]]
- [[mod_eq_predecessor_cancel]]
- [[remainder_decomposition_to_mod_eq]] · [[beta_at_to_mod_eq]]
- [[mod_eq_bounded_unique]] · [[mod_eq_to_remainder_decomposition]]
- [[beta_at_of_mod_eq_bound]]
- [[beta_modulus_nonzero]] · [[beta_at_self_of_bound]]
- [[beta_at_exists]] · [[beta_at_unique]] · [[beta_at_exists_unique]]
- [[binary_crt]] · [[binary_crt_remainders]] · [[binary_crt_beta_pair]]
- [[beta_modulus_coprime_base]]
- [[common_divisor_beta_moduli_divides_gap_times_c]]
- [[beta_moduli_coprime_of_gap_dvd]] · [[binary_crt_beta_pair_of_gap_dvd]]
- [[bounded_common_multiple_step]] · [[bounded_common_multiple_exists]]
- [[beta_moduli_coprime_of_lt_bounded_common_multiple]]
- [[beta_moduli_pairwise_coprime_bounded]]
- [[bounded_beta_moduli_pairwise_coprime_exists]]
- [[coprime_mul_left]] · [[coprime_mul_right]]
- [[mod_eq_of_mod_eq_multiple]] · [[binary_crt_fold_step]]
- [[beta_accumulated_product_step]] · [[beta_crt_prefix_congruence_step]]
- [[beta_crt_prefix_invariant_step]] · [[bounded_beta_crt_prefix_invariant]]
- [[bounded_beta_crt_for_existing_code]]

The original β-pair node constructs one code for two bounded values under an
explicit coprimality premise. The new conditional chain discharges that premise
when `j = i + gap` and `gap | c`. The bounded common-multiple theorem
constructs a nonzero `c` divisible by every positive natural at most a
given bound.

This is deliberately not a claim that arbitrary β moduli are pairwise
coprime: that statement is false (for `c = 1`, indices 1 and 4 give
moduli 3 and 6). The checked bounded-prefix theorem instead first constructs a
suitable common-multiple base, then proves all distinct positions through the
chosen bound pairwise coprime. Product coprimality, congruence descent, and one
binary CRT preservation step are checked too. The bounded invariant chain folds
the accumulated product and decoded congruences through a bounded prefix by
ordinary induction. Its wrapper assumes an already existing `BetaAt` code; it
does not by itself code an arbitrary finite sequence. The later checked
exclusive-prefix recoding and extension layer closes that separate gap.

## Checked finite β coding, Products, and factorization

- `beta_prefix_extend` — rebase a decoded finite prefix and append one value
- `beta_prefix_product_trace_exists` — construct an exact β-coded product trace
- `beta_product_exists` · `beta_product_functional` · `beta_product_exists_unique`
- `beta_product_zero` · `beta_product_succ_decompose` · `beta_product_succ_append`
- `greatest_prime_divisor_search` · `greatest_prime_divisor_exists`
- `greatest_prime_divisor_quotient_bound` · `greatest_prime_divisor_descent`
- `beta_canonical_append_general` — preserve Product, `AllPrime`, and `Sorted`
- `prime_factorization_existence` — 43,973 nodes/depth 98
- `prime_factorization_uniqueness` — 29,789 nodes/depth 82
- `fundamental_theorem_of_arithmetic` — 73,767 nodes/depth 99/2,184 Cuts

## Checked prime nodes

- [[prime_two]] — the fully expanded factor-pair predicate for the numeral two
- [[prime_divisor_eq_one_or_self]] — every divisor of a prime is one or that prime
- [[euclid_prime_dvd_product]] — Euclid's lemma with primality and divisibility expanded

## Checked constructive decisions and prime search

- [[eq_decidable]] — constructive equality decision
- [[multiple_decidable_nonzero]] · [[multiple_decidable]] — constructive divisibility decisions
- [[factor_nonzero_left]] · [[proper_factor_lt]] — nonzero and strict-descent factor facts
- [[factor_property_succ]] · [[factor_search_up_to]] — bounded factor-pair search
- [[prime_nonzero]] · [[prime_or_composite]] · [[prime_decidable]]
- [[prime_divisor_exists_up_to]] · [[prime_divisor_exists]] — bounded and public prime-divisor existence
- [[constructive-prime-unboundedness]] — a prime above every bound from a common multiple and its successor

The native [[godel-beta-sequence|β-coded FTA]] and constructive
[[constructive-prime-unboundedness|prime unboundedness]] are checked at this
integration checkpoint. Remaining boundaries are different: primitive lists,
finite maps, and generic powers remain absent; conventional
integer-coefficient Bézout is unavailable, while the four-natural balanced
relation is checked.

## Executable and documentary views

- Runtime: `peano-lab/py/peano_lab/library/theorems.py`
- Catalog: `research/arithmetic-library/catalog.json`
- Generated snapshot: `artifacts/peano-library/catalog-v1.json`
- Dependency graph: `artifacts/peano-library/dependency-graph.mmd`
- Line-by-line dashboard: [[pa-proof-explorer]]
- Book: `book/arithmetic-library/`
- Plan: `PLAN/10_arithmetic_library.md`

## Up

[[peano-lab-moc]] · [[00-index]]

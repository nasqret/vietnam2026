---
title: Native quadratic reciprocity — Map of Content
tags: [moc, peano-arithmetic, quadratic-reciprocity, number-theory]
---

# Native quadratic reciprocity

This map follows the checked campaign from the existing arithmetic spine to a
fully expanded, intuitionistic first-order PA certificate for quadratic
reciprocity. No Legendre-symbol function, integers, powers, finite sets or
lists are added to the object language.

## Checked entrance layer

- [[parity_cases]]
- [[even_odd_exclusive_pointwise]]
- [[even_not_odd]] · [[odd_not_even]]
- [[successor_odd_of_even]] · [[successor_even_of_odd]]
- [[even_add_even]] · [[even_add_odd]] · [[odd_add_even]] · [[odd_add_odd]]
- [[even_mul_left]] · [[even_mul_right]] · [[odd_mul_odd]]
- [[odd_half_exists_unique]]
- [[odd_mod4_cases]] · [[mod4_one_three_exclusive_pointwise]]
- [[mod4_one_is_odd]] · [[mod4_three_is_odd]]
- [[prime_ne_two_is_odd]]
- [[mod_eq_decidable_from_remainders]] · [[mod_eq_decidable_nonzero]]

## Checked small-modulus classifications

- [[qres_mod3_canonical_iff]] · [[not_qres_mod3_two]]
- [[qres_mod5_canonical_iff]] · [[not_qres_mod5_two]] · [[not_qres_mod5_three]]
- [[qres_mod7_canonical_iff]] · [[not_qres_mod7_three]]
- [[not_qres_mod7_five]] · [[not_qres_mod7_six]]

## Existing arithmetic prerequisites

- [[division_remainder_exists]] · [[division_remainder_unique]]
- [[mod_eq_refl]] · [[mod_eq_symm]] · [[mod_eq_trans]] · [[mod_eq_mul]]
- [[mod_eq_bounded_unique]] · [[mod_eq_to_remainder_decomposition]]
- [[coprime_balanced_bezout]] · [[gauss_coprime_cancel]]
- [[euclid_prime_dvd_product]]
- [[beta_prefix_extend]] · [[beta_product_exists_unique]]

## Checked prime-unit layer

- [[prime_coprime_or_divides]] · [[prime_not_divides_coprime]]
- [[distinct_primes_coprime]]
- [[coprime_balanced_mod_inverse]] · [[coprime_mod_inverse]]
- [[mod_eq_cancel_coprime]]
- [[prime_mod_inverse]] · [[prime_mod_cancel]]

## Active finite-fold layer

The authoring surface has exact expanded relations for `Repeat`, `Range`,
`Pow`, `Sum`, `AllBits`, and `BitCount`. The first checked fold certificates
are:

- [[beta_repeat_empty]] · [[beta_repeat_succ_extend]] · [[beta_repeat_exists]]
- [[beta_repeat_entry_eq]] · [[beta_repeat_transport_entry]]
- [[pow_exists]] · [[pow_zero]] · [[pow_functional]]
- [[pow_successor_decompose]]
- [[beta_range_empty]] · [[beta_range_succ_extend]] · [[beta_range_exists]]
- [[beta_range_entry_eq]] · [[beta_range_transport_entry]]
- [[beta_prefix_sum_trace_exists]] · [[beta_sum_exists]]
- [[beta_sum_trace_functional]] · [[beta_sum_functional]]
- [[beta_sum_exists_unique]] · [[beta_sum_zero]] · [[beta_sum_succ_decompose]]
- [[all_bits_zero]] · [[all_bits_prefix_succ]] · [[all_bits_last_succ]]
- [[bit_count_exists]] · [[bit_count_functional]] · [[bit_count_zero]]
- [[bit_count_succ_decompose]] · [[bit_count_bounded]]
- [[beta_product_pointwise_mod_congruent]]
- [[beta_sum_pointwise_mod_congruent]]

## Checked factorial and power bridges

- [[factorial_exists]] · [[factorial_functional]] · [[factorial_zero]]
- [[factorial_succ_decompose]]
- [[pow_one_from_zero_successor]] · [[pow_one]]
- [[pow_successor_pair_mul]] · [[pow_mod_congruent]]
- [[pow_two_from_one_successor]] · [[pow_two]] · [[pow_add]] · [[pow_mul_exp]]

## Checked Gauss-sign bridge

- [[predecessor_square_mod_one]]
- [[even_successor_to_odd]] · [[odd_successor_to_even]]
- [[pow_predecessor_parity_mod]]

## Body-green parity and reciprocity clients

- [[parity-transport]] — sum classification, modulo-two transport,
  odd-division parity, and odd-half/modulo-four equivalences; four focused
  suites pass `16/16` in 1.24 seconds
- [[gauss-product-composition]] — bounded and arbitrary actual-`QRes` Gauss
  endpoints at `597/53` and `547/49` nodes/depth
- [[gauss-eisenstein-reciprocity]] — exact pointwise/sum alignment, the
  two-prime data package, and the exact same/opposite/combined QR surfaces

These links describe dependency-curried, unregistered and unadmitted
candidates. They are deliberately separate from the checked registry layers.

## Checked positive half-range

- [[beta_range_injective]] · [[beta_half_range_entry_bounds]]
- [[beta_half_range_mod_eq_value]] · [[beta_half_range_mod_injective]]

## Checked finite permutation completeness

- [[beta_prefix_replace_exists]]
- [[beta_prefix_swap_last_from_entries]] · [[beta_prefix_swap_last_exists]]
- [[beta_prefix_swap_last_reflect]]
- [[finite_swap_last_bounded]] · [[finite_swap_last_injective]]
- [[finite_swap_last_surjective_back]]
- [[finite_contains_decidable]] · [[finite_no_top_successor_gate]]
- [[finite_bounded_injective_surjective]]

## Checked product replacement and swap transport

- [[beta_prefix_replace_reflect]]
- [[beta_product_replace_balance]]
- [[beta_product_swap_last_invariant]]

## WMI-isolated proof laboratory

These entries are source candidates, not vault theorem notes and not checked
registry facts. Their status changes only after a content-addressed WMI replay
and a separate pinned admission replay.

- Finite complement count: `complementary_bit_counts_add_length` proves that
  two length-`l` `BitCount` prefixes with decoded pairs `(0,1)` or `(1,0)`
  satisfy `n+m=l`. Its 112-command body is `220/46` nodes/depth, with `211`
  objects, `219` edges and `9` reused objects; the no-DNE focused audit passes
  `3/3` in 1.47 seconds. This is one-dimensional only, not a nested
  transpose/Fubini theorem
- General product reindexing: `beta_product_reindex_fixed_last` and
  `beta_product_permutation_invariant`
- Fermat range/product tranche: `beta_range_one_entry_eq_succ`,
  `beta_product_pointwise_coprime`, and `prime_range_product_coprime`
- Fermat residue-map tranche: `beta_successor_lift_exists` and
  `prime_mul_index_map_exists_up_to`
- Fermat residue-reindex tranche: `fermat_index_map_bounded`,
  `prime_mul_index_map_injective`,
  `beta_successor_range_reindex_aligned`,
  `beta_successor_range_scale_mod`, and the packaged rung
  `prime_mul_residue_reindex_exists`
- Fermat product tranche: `beta_product_pointwise_scale_mod` and
  `prime_mul_residue_product_balance`
- Fermat endpoints: `fermat_predecessor_exponent_mod_one` and
  `fermat_little_all_inputs`; both are isolated candidates. Dedicated
  `fermat-endpoints` discovery job `172837`, bound to snapshot
  `c7cc39f94b2cb0ae5542f89b3ddec947d84c55627168e07851c62da36f51bd34`,
  was cancelled stale after zero CPU, as were original reindex/balance jobs
  `172769` and `172770`. Corrected snapshot
  `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`
  backs jobs `172988` (reindex, 16 GiB/2 hours), `172989` (balance,
  16 GiB/2 hours), and `172990` (endpoints, 32 GiB/4 hours); all were pending
  at submission. There is no pass or admission result
- Fermat preflight: all 21 finite-product plus Fermat bodies pass after fixing
  a missing second rewrite in `beta_successor_range_reindex_aligned` and an
  invalid locally repackaged `hprojection` in
  `prime_mul_residue_product_balance`. Key nodes/depth are `86/34`, `62/32`,
  `106/40`, `93/39`, `93/34`, and `104/30` for reindex alignment, scale,
  reindex existence, balance, predecessor Fermat, and all-input Fermat.
  Nine bounded structural gates pass across reindex, balance, and endpoints.
  `candidate_validation.replay_candidate_bodies` performs this dependency-
  curried kernel check without closing dependencies, returns structural/
  identity metrics, and has three passing unit tests. It is explicitly
  non-admitting; these are body/structure receipts, not closed replay
- Wilson fixed-point arithmetic: `prime_bounded_square_one_cases` is an
  isolated candidate. It rewrites positive `x` as `S t`, derives
  `p | t * (t + 2)`, applies native Euclid, and uses the bounds to conclude
  `x = 1 \/ x = n`. The UI-only `ring` call has been removed in favor of an
  explicit native equality/rewrite derivation; its exact 16-dependency
  boundary, including `mul_succ_left`, is recorded in the design note.
  Five-gate `wilson-square-one` discovery job `172855`, snapshot
  `396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`,
  was cancelled stale after zero CPU. Its body-only receipt is 182 nodes/depth
  48 and its three structural gates passed. Replacement job `172966`, common
  snapshot `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  is `PENDING (Priority)` with zero CPU; this is not a pass or admission
- Wilson inverse map: four isolated pointwise candidates provide mate
  existence, bounded modular uniqueness, zero-based index uniqueness, and
  symmetry; three isolated prefix candidates append one β-decoded mate,
  construct every bounded length, and specialize to the full prime-
  predecessor prefix. `InvIdx(p,n,i,j)` means `i<n`, `j<n`, and
  `(S i)*(S j) ≡ 1 (mod p)`; `InvPrefix` existentially β-decodes such a `j`
  at every position below its length. Five-gate `wilson-inverse-prefix`
  discovery job `172899` recursively closes all seven candidates from snapshot
  `1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`.
  Cheap body replay found two existential-binder errors, so it was cancelled
  after zero CPU. The fixes are in snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
  replacement job `172975` is pending. There is no pass, pinned metric set,
  or admission
- Wilson extensional inverse map: six isolated candidates establish decoded
  soundness, extensionality, involution, injectivity, surjectivity, and fixed-
  index classification. The first five are prime-free; only
  `prime_inverse_prefix_fixed_cases` assumes primality and concludes
  `i = 0 \/ S i = n`. Five-gate `wilson-inverse-involution` discovery job
  `172920` recursively closes 14 specs from snapshot
  `cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`.
  It was cancelled stale after zero CPU. First replacement `172967`, from the
  common snapshot, was also cancelled after zero CPU when the prefix changed.
  Corrected job `172976`, from snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending; there is no pass, pinned metric set, or admission
- Wilson inverse endpoints: `inverse_prefix_zero_fixed` and
  `inverse_prefix_last_fixed` decode the fixed entries at indices `0` and
  `k` when `p=S n` and `n=S k`;
  `prime_inverse_prefix_exact_endpoints` packages both facts with the converse
  `i<n -> At(i,i) -> i=0 \/ i=k`. Prime `2` is represented honestly by
  `k=0`, so the endpoints coincide. The five-gate
  `wilson-inverse-endpoints` suite recursively closes 17 isolated specs.
  Discovery job `172927`, snapshot
  `7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`,
  was cancelled stale after zero CPU. First replacement `172968`, from the
  common snapshot, was also cancelled after zero CPU. Corrected job `172977`,
  from snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending.
  Syntax and the first three bounded cheap gates passed locally; heavy replay,
  profiling, and mutations remain WMI-only. There is no pass, pinned receipt,
  or admission. The runner now exposes seven focused suites and 66 full gates
- Wilson nonendpoint inverse orbits:
  `prime_inverse_prefix_nonendpoint_not_fixed` proves that a decoded mate
  differs from a source satisfying `~(i=0) /\ ~(S i=n)`;
  `prime_inverse_prefix_nonendpoint_mate` uses involution and the two fixed
  endpoint entries to prove the mate satisfies the same predicate. The scope
  is deliberately honest at prime `2`: endpoint coincidence remains allowed,
  and no nonendpoint index is asserted to exist. The five-gate
  `wilson-inverse-orbit` suite recursively closes 19 isolated specs. Discovery
  job `172932`, snapshot
  `5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`,
  was cancelled stale after zero CPU. Cheap body replay caught and fixed an
  apply-to-negation error. First replacement `172970`, from the common
  snapshot, was also cancelled after zero CPU. Corrected job `172978`, from
  snapshot `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending.
  Syntax and the first three cheap gates passed locally; both cold replays,
  profiling, and mutations remain WMI-only. There is no pass, pinned receipt,
  or admission. The runner now exposes eight focused suites and 71 full gates
- Wilson body receipts: all 19 candidate bodies pass. Layered nodes/depth are
  square `182/48`; point `55/22`, `70/28`, `50/21`, `20/12`; prefix `76/29`,
  `64/25`, `29/16`; involution `44/23`, `49/25`, `80/29`, `55/29`, `31/22`,
  `83/31`; endpoints `76/23`, `54/23`, `104/32`; and orbit `45/26`, `206/40`.
  Twelve bounded structural gates pass across prefix, involution, endpoints,
  and orbit—three per suite. They are not closed recursive replay or admission
- Wilson adjacent pair products: `beta_product_double_succ_decompose` splits
  an exact product at length `S(S k)` into a `k`-prefix and its final two
  decoded factors; `beta_adjacent_unit_pairs_product_one` folds `m` adjacent
  pairs, each congruent to one modulo `p`, to prove the product of the first
  `m+m` factors is congruent to one. All five corrected suite gates passed
  locally in 5.4 seconds with two cold passes. Metrics are 1,317 nodes/depth
  63/844 objects and 4,372 nodes/depth 64/1,290 objects; graph hash
  `622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
  source hash
  `193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.
  Authoritative WMI job `172946`, snapshot
  `9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`,
  is queued/pending on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; the
  independent WMI admission receipt is still required. Jobs `172936` and
  `172943` were cancelled before start as superseded known-broken snapshots
  with two separate missing third rewrites
- Wilson PairOrder extension: nine isolated candidates append and reflect two
  β entries, choose a fresh nonendpoint constructively, extract its unused
  inverse mate, preserve orbit closure/nonendpoint range/injectivity, and
  package one choose-and-append step. Body nodes/depth are `63/27`, `115/32`,
  `113/30`, `138/43`, `34/20`, `167/38`, `63/31`, `202/36`, and `191/53`.
  The later paired-history iteration and successor-lift/product layer are now
  body-green. Their seven iteration bodies measure `34/16`, `38/17`, `19/15`,
  `114/31`, `122/40`, `169/39`, `52/26`; the four lift/product bodies measure
  `17/11`, `124/38`, `41/31`, `65/32`. Four terminal transport bodies then
  prove the canonical nonendpoint product equality at `80/30`, `152/42`,
  `79/39`, `188/65`. Seven endpoint bodies then prove the exact factorial
  Wilson congruence at `30/15`, `258/45`, `63/29`, `21/16`, `104/30`,
  `94/35`, and `110/31`, with prime `2` handled separately; see
  [[wilson-pair-order]] and the
  [PairOrder encoding](../../research/arithmetic-library/pair-order-encoding.md).
- Euler scaled inverse: ten isolated candidates give bounded pointwise
  existence/uniqueness for `x*y == a (mod p)`, symmetry, involution,
  fixed-point/square equivalence and fixed-point freedom under `~QRes`. Body
  nodes/depth are `36/17`, `30/19`, `58/25`, `126/34`, `74/24`, `31/12`,
  `28/19`, `38/15`, `17/15`, and `24/15`. Three full-prefix bodies add
  extension, bounded existence and complete-map existence at `105/36`,
  `81/33`, and `40/23`. Soundness, extensionality, fixed-point freedom,
  predecessor extraction, involution and decoded injectivity then pass at
  `58/25`, `54/26`, `36/27`, `67/36`, `91/39`, and `77/36`; see
  [[euler-scaled-inverse-map]] and the
  [Euler entrance ladder](../../research/arithmetic-library/euler-scaled-inverse.md).
  The generic adjacent-target product fold is body-green at `171/47`, and the
  independent quadratic-residue branch of Euler is body-green at `48/18`
  plus `148/39`. The representation-correct shifted PairOrder entrance adds
  four one-orbit bodies at `34/20`, `184/40`, `107/38`, and `190/52`; ten
  terminal-iteration bodies end at `155/39`, `41/25`, and `64/26`. The five
  nonresidue endpoint bodies are `132/39`, `144/45`, `136/52`, `61/34`, and
  `49/30`; they successor-lift the adjacent targets, identify the lifted
  product with factorial, apply Wilson, and prove the bounded public
  `~QRes -> half-power == p-1` endpoint. Their focused audit passes `4/4` in
  4.39 seconds and the related stack passes `16/16` in 12.19 seconds. All
  remain constructive, no-DNE, dependency-curried, unregistered and
  unadmitted. Seven further package bodies at `20/13`, `65/19`, `56/25`,
  `120/39`, `92/30`, `91/37`, and `80/31` prove the full reduced-input iff
  pair `QRes <-> half-power == 1` and
  `~QRes <-> half-power == p-1`; their focused audit passes `4/4` in 1.67
  seconds and the combined bounded stack passes `12/12` in 7.62 seconds. The
  six arbitrary-representative bodies—`nondivisor_canonical_remainder_exists`,
  `quadratic_residue_mod_equiv`, `pow_congruent_base_witness`,
  `arbitrary_euler_criterion_residue_iff`,
  `arbitrary_euler_criterion_nonresidue_iff`, and
  `arbitrary_euler_criterion_complete`—then derive a nonzero canonical
  remainder, transport `QRes`, construct and transport a relational power,
  and prove `QRes(p,a) <-> A==1` together with
  `~QRes(p,a) <-> A==p-1` for every `a` with `p` not dividing `a`.
  Their dependency/command/node/depth receipts are `3/39/49/20`,
  `2/31/38/17`, `2/25/29/22`, `7/92/140/36`, `7/98/146/37`, and
  `2/33/75/29`; the corresponding object/edge/reuse tails are `49/48/0`,
  `38/37/0`, `29/28/0`, `140/139/0`, `146/145/0`, and `75/74/0`.
  Their focused hash/contract/body audit passes `4/4` in 2.04 seconds, and the
  combined Euler selection passes `16/16` in 9.96 seconds. The terminal,
  bounded-equivalence, and unreduced-representative gaps are body-green; WMI
  closure/mutations/admission remain.
- Signed-half representatives: isolated candidates
  `odd_upper_remainder_reflection` and
  `gauss_pointwise_signed_half_representative` have body-only receipts
  125/34 and 116/38 nodes/depth. Their three bounded structural gates passed.
  Focused job `172964`, from common snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  is `PENDING (Priority)` with zero CPU
- Finite omission: the eight isolated candidates have body-only nodes/depth,
  in dependency order, `73/22`, `69/27`, `58/23`, `21/15`, `89/31`,
  `149/43`, `24/16`, and `27/18`. Their three bounded structural gates passed.
  Focused job `172965`, from the common snapshot, is `PENDING (Priority)` with
  zero CPU
- Current focused tranche: exact snapshot
  `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`
  produced pending zero-CPU jobs `173015` (`euler-scaled-inverse`), `173016`
  (`gauss-signed-prefix`), and `173017` (`wilson-pair-order`). All three
  test-only validations returned exit zero after replacing `bash -l -s` with
  `bash -s`; the WMI login-shell logout hook had overwritten successful
  validation status. At that first frozen checkpoint the runner selected 101
  gates across 22 test-source modules and exposed 14 focused five-gate suites
  plus `full`
- Second frozen checkpoint: snapshot
  `fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`
  produced pending zero-CPU jobs `173021` (`gauss-magnitude-permutation`) and
  `173022` (`wilson-pair-order-induction`). The live runner selects 111 gates
  across 24 test sources and exposes 16 focused five-gate suites plus `full`
- Gauss magnitude endpoint: eleven candidates prove range, collision control,
  injectivity, predecessor recoding and finite surjectivity. Body nodes/depth
  are `39/25`, `48/24`, `96/34`, `169/50`, `626/70`, `157/45`, `31/25`,
  `87/30`, `48/20`, `60/31`, `39/21`; see
  [magnitude permutation](../../research/arithmetic-library/gauss-magnitude-permutation.md)
- PairOrder bounded state: fifteen candidates preserve orbit closure,
  boundedness, nonendpoint range and injectivity, then prove terminal coverage.
  Body nodes/depth are `95/40`, `19/12`, `69/27`, `90/42`, `23/19`, `18/14`,
  `20/16`, `22/18`, `64/19`, `8/8`, `12/9`, `266/44`, `33/20`, `72/37`,
  `51/36`. Full iteration, successor lift and canonical product transport are
  now body-green; the seven-body endpoint/Wilson capstone is body-green too
- Product frontier: three magnitude-alignment bodies pass at `51/28`,
  `127/39`, `72/34`; two sign-product/power bodies at `35/24`, `259/46`.
  Sign-factor and pointwise-product recoding are now body-green. The composed
  balance and cancellation bodies prove `A*P == P*R (mod p)` and
  `A == R (mod p)` at `148/70` and `156/87`; see
  [[gauss-product-composition]]. The bounded actual-residue endpoint then
  proves `QRes(p,a) iff Even(e)` and `not QRes(p,a) iff Odd(e)` at `597/53`;
  the arbitrary-prime-unit wrapper proves the same at `547/49`. Their audits
  pass together at `9/9` in 13.64 seconds. This remains body-only evidence,
  not recursive closure or admission
- Eisenstein division prefix: `beta_division_prefix_extend` and
  `beta_division_prefix_exists` construct beta-coded quotient and bounded
  remainder traces for any finite beta source at `132/41` and `71/30`.
  The exact half-range scaling/division/sum follow-on passes at `34/24`,
  `71/40`, and `52/28`. Noncollision and constructive orientation across the
  half rectangle pass at `72/30`, `77/34`, and `53/34`; the concrete
  row indicator/count ladder then passes at `46/29`, `71/27`, `58/23`,
  `53/34`, `27/16`, `43/23`, and `63/29`. Eight outer-prefix/sum bodies now
  construct the nested rectangle total. The generic division threshold is
  `92/30`; sound remainder-nonzero wrappers are `47/21`, `45/24`, `45/28`;
  and the odd-half gap/quotient bound are `160/45`, `67/29`. The false
  cross-half remainder claim is pinned by `p=3,q=7,i=2`. The eight-body exact
  initial-segment `BitCount` ladder now passes at `23/12`, `63/25`, `40/19`,
  `25/14`, `41/21`, `91/28`, `160/37`, and `49/21`; its focused audit is
  `11/11` in 2.09 seconds. The dependency-free `beta_sum_transport_prefix`
  body is `59/29` with `44` commands and reuses an exact `Sum` trace across
  pointwise-equal decoded prefixes. Generic exact addition
  `beta_sum_pointwise_add` is `195/57` with `127` commands and proves endpoint
  addition from decoded pointwise addition. Constant-prefix evaluation and
  exact existence are `85/32` and `33/21`, producing the endpoint `l*a` for
  a length-`l` `Repeat(a)` prefix. The one-dimensional complementary-count
  body is `220/46` with `112` commands and proves that matched complementary
  row counts sum to their common length. Four row-quotient bodies at `78/36`,
  `95/45`, `111/55`, and `119/72` now identify each semantic row count with
  its decoded quotient; their focused audit passes `4/4` in 3.40 seconds.
  Three outer-sum bodies at `104/52`, `73/54`, and `67/51` now transport the
  quotient `Sum` to the semantic rectangle prefix and prove endpoint equality;
  the bridge works symmetrically after swapping the primes and halves. A
  `95/33` transposed-cell body and `116/58` outer-cell witness expose
  complementary `(i,j)`/`(j,i)` bits through both nested prefixes; their
  combined audit passes `6/6` in 2.08 seconds. Six further bodies construct a
  complete fixed-index transposed column:
  `eisenstein_transposed_outer_column_choices`,
  `eisenstein_transposed_column_prefix_extend`,
  `eisenstein_transposed_column_prefix_exists`,
  `eisenstein_transposed_column_prefix_all_bits`,
  `eisenstein_transposed_column_pointwise_complement`, and
  `eisenstein_row_transposed_column_count_partition`. The endpoint returns a
  provenance-carrying column `BitCount m` and proves `n+m=k` against the
  original row count. In exact
  `dependencies / commands / nodes / depth / objects / edges / reused`
  order, their receipts are `2/37/42/26/42/41/0`,
  `2/55/80/31/80/79/0`, `5/56/64/29/64/63/0`,
  `1/48/56/33/56/55/0`, `2/64/87/47/87/86/0`, and
  `6/105/117/56/117/116/0`; the focused audit passes `5/5` in 5.05 seconds.
  Every column entry retains the swapped outer decode, existential inner row
  code/scale and semantics, its `BitCount`, and the decoded cell, rather than
  asserting a bare beta code. The nested two-dimensional transpose/Fubini
  layer is now body-green: it encodes and sums the column counts, identifies
  that sum with the swapped total, and proves the semantic rectangle identity.
  `distinct_odd_prime_eisenstein_quotient_sum_identity` then preserves both
  decoded quotient systems and proves the exact `Q+U=h*k` endpoint at
  `145/68`. See
  [[eisenstein-division-prefix]] and the
  [division-prefix design](../../research/arithmetic-library/eisenstein-division-prefix.md)
- Gauss--Eisenstein parity alignment: the exact finite-sum swap/reindex ladder
  has bodies `327/59`, `133/50`, `85/33`, and `631/88` nodes/depth.
  `gauss_eisenstein_prefix_pointwise_mod_two` is `250/61` with statement hash
  prefix `84b039`; the final sum-cancellation endpoint preserves all beta
  parameters and proves `Q congruent e (mod 2)` at `89/65`. Pointwise plus sum
  suites pass `12/12` in 17.47 seconds
- Two-prime and final QR packaging:
  `odd_prime_gauss_eisenstein_orientation_data_exists` is
  `5/102/139/67` and
  `distinct_odd_primes_gauss_eisenstein_data_exists` is `4/150/222/77` in
  dependencies/commands/nodes/depth order. Exact same- and opposite-status QR
  bodies are `2/46/73/33` each; the combined public endpoint is
  `3/65/113/35`. It constructs pair data once and calls both conditional
  clients directly. The downstream integration passes `20/20` in 27.25
  seconds.
  All remain dependency-curried, unregistered and unadmitted; see
  [[gauss-eisenstein-reciprocity]]
- Closure architecture: the exact endpoint graph has 557 specifications,
  1,791 edges, 45 layers, root depth 44, and 191,669 theorem occurrences under
  recursive expansion. Its rigorous 731,482-node lower bound exceeds the
  500,000-node policy. The preferred [[layered-cut-bundle]] places each body
  once in one of 45 balanced conjunction packages and uses only existing
  projections and contextual Cuts; the unchanged kernel still performs the
  final empty-context check. The full WMI artifact is not yet constructed or
  admitted. Static exact-graph integration is green at two deliberately
  weaker levels: a rejected dummy scaffold is `13,715/56` nodes/depth with
  13,158 fixed glue nodes, while an accepted distinct-marker topology
  surrogate is `19,088/74`, with package formulas `19,297/18`. Its unique
  local-ID-derived targets and one dependency Cut/Hyp check per premise force
  every real projection ID/direction and declared dependency order. Neither
  contains real QR bodies and neither proves QR. The
  [[closed-proof-dag]] is fallback only
- WMI Book harness: independent static audit findings were remediated; the
  harness is ready for test-only validation. No transfer, submission,
  dependency installation or build is claimed
- Evidence boundary: laptop execution is limited to static checks,
  dependency-curried body preflight, and small synthetic compiler tests under
  a hard 60-second cap. Full layered closure, profiles, mutations, browser
  replay and book builds remain WMI-only. Body and structural receipts,
  test-only validation, and pending jobs are not closed-certificate admission
  and admit no theorem
- WMI queue priority: superseded full jobs `172707`, `172716`, `172722`, and
  `172737` are user-held, not cancelled, while focused prerequisite jobs run.
  Release the reversible holds after focused discovery results settle
- Design: [Fermat/Wilson and the remaining reciprocity spine](../../research/arithmetic-library/fermat-wilson-next-tranche.md)
- Reindex architecture: [product permutation invariance](../../research/arithmetic-library/product-permutation-invariance.md)
- Execution and admission policy: [WMI QR replay](../../research/arithmetic-library/wmi-qr-replay.md)
- Candidate source: [Fermat residue products](../../peano-lab/py/peano_lab/library/fermat_residue_product_candidate.py)
- Candidate source: [Fermat residue maps](../../peano-lab/py/peano_lab/library/fermat_residue_map_candidate.py)
- Candidate source: [Fermat residue reindexing](../../peano-lab/py/peano_lab/library/fermat_residue_reindex_candidate.py)
- Candidate source: [Fermat scale products](../../peano-lab/py/peano_lab/library/fermat_scale_product_candidate.py)
- Candidate source: [Fermat product balance](../../peano-lab/py/peano_lab/library/fermat_product_balance_candidate.py)
- Candidate source: [Fermat endpoints](../../peano-lab/py/peano_lab/library/fermat_endpoints_candidate.py)
- Candidate source: [Wilson square-one classification](../../peano-lab/py/peano_lab/library/wilson_square_one_candidate.py)
- Candidate source: [Wilson pointwise inverse indices](../../peano-lab/py/peano_lab/library/wilson_inverse_point_candidate.py)
- Candidate source: [Wilson inverse β-prefixes](../../peano-lab/py/peano_lab/library/wilson_inverse_prefix_candidate.py)
- Candidate source: [Wilson extensional inverse involution](../../peano-lab/py/peano_lab/library/wilson_inverse_involution_candidate.py)
- Candidate source: [Wilson inverse endpoints](../../peano-lab/py/peano_lab/library/wilson_inverse_endpoints_candidate.py)
- Candidate source: [Wilson nonendpoint inverse orbits](../../peano-lab/py/peano_lab/library/wilson_inverse_orbit_candidate.py)
- Candidate source: [Wilson adjacent pair products](../../peano-lab/py/peano_lab/library/wilson_pair_product_candidate.py)
- Candidate source: [Wilson PairOrder extension](../../peano-lab/py/peano_lab/library/wilson_pair_order_candidate.py)
- Candidate source: [Euler scaled inverse](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_candidate.py)
- Candidate source: [Euler scaled-inverse prefix](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_prefix_candidate.py)
- Candidate source: [Euler prefix extensionality](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_prefix_extensional_candidate.py)
- Candidate source: [Euler adjacent-target product](../../peano-lab/py/peano_lab/library/euler_pair_product_candidate.py)
- Candidate source: [Euler quadratic-residue branch](../../peano-lab/py/peano_lab/library/euler_criterion_residue_candidate.py)
- Candidate source: [Euler shifted PairOrder entrance](../../peano-lab/py/peano_lab/library/euler_scaled_pair_order_entrance_candidate.py)
- Candidate source: [Euler terminal PairOrder iteration](../../peano-lab/py/peano_lab/library/euler_scaled_pair_order_iteration_candidate.py)
- Candidate source: [Euler nonresidue endpoint](../../peano-lab/py/peano_lab/library/euler_nonresidue_endpoint_candidate.py)
- Focused test: [Euler nonresidue endpoint](../../peano-lab/py/tests/test_euler_nonresidue_endpoint_candidate.py)
- Candidate source: [Complete bounded Euler criterion](../../peano-lab/py/peano_lab/library/euler_criterion_bounded_candidate.py)
- Focused test: [Complete bounded Euler criterion](../../peano-lab/py/tests/test_euler_criterion_bounded_candidate.py)
- Candidate source: [Arbitrary-representative Euler criterion](../../peano-lab/py/peano_lab/library/euler_criterion_arbitrary_candidate.py)
- Focused test: [Arbitrary-representative Euler criterion](../../peano-lab/py/tests/test_euler_criterion_arbitrary_candidate.py)
- Candidate source: [Gauss signed-half representatives](../../peano-lab/py/peano_lab/library/gauss_signed_half_candidate.py)
- Candidate source: [Gauss signed prefixes](../../peano-lab/py/peano_lab/library/gauss_signed_prefix_candidate.py)
- Candidate source: [Gauss magnitude permutation](../../peano-lab/py/peano_lab/library/gauss_magnitude_permutation_candidate.py)
- Candidate source: [Gauss magnitude product alignment](../../peano-lab/py/peano_lab/library/gauss_magnitude_product_candidate.py)
- Candidate source: [Gauss sign product](../../peano-lab/py/peano_lab/library/gauss_sign_product_candidate.py)
- Candidate source: [Gauss product composition](../../peano-lab/py/peano_lab/library/gauss_product_composition_candidate.py)
- Candidate source: [Bounded complete Gauss lemma](../../peano-lab/py/peano_lab/library/gauss_lemma_bounded_candidate.py)
- Focused test: [Bounded complete Gauss lemma](../../peano-lab/py/tests/test_gauss_lemma_bounded_candidate.py)
- Candidate source: [Arbitrary complete Gauss lemma](../../peano-lab/py/peano_lab/library/gauss_lemma_arbitrary_candidate.py)
- Focused test: [Arbitrary complete Gauss lemma](../../peano-lab/py/tests/test_gauss_lemma_arbitrary_candidate.py)
- Candidate source: [Finite omission](../../peano-lab/py/peano_lab/library/finite_omission_candidate.py)
- Candidate source: [Wilson terminal product](../../peano-lab/py/peano_lab/library/wilson_terminal_product_candidate.py)
- Candidate source: [Wilson endpoint restoration](../../peano-lab/py/peano_lab/library/wilson_endpoint_restoration_candidate.py)
- Candidate source: [Eisenstein division prefix](../../peano-lab/py/peano_lab/library/finite_division_prefix_candidate.py)
- Candidate source: [Eisenstein scaled division](../../peano-lab/py/peano_lab/library/eisenstein_scaled_division_candidate.py)
- Candidate source: [Eisenstein lattice orientation](../../peano-lab/py/peano_lab/library/eisenstein_lattice_orientation_candidate.py)
- Candidate source: [Eisenstein row indicator](../../peano-lab/py/peano_lab/library/eisenstein_row_indicator_candidate.py)
- Candidate source: [Eisenstein nested rectangle count](../../peano-lab/py/peano_lab/library/eisenstein_rectangle_count_candidate.py)
- Candidate source: [Eisenstein division threshold](../../peano-lab/py/peano_lab/library/eisenstein_division_threshold_candidate.py)
- Candidate source: [Eisenstein remainder nonzero](../../peano-lab/py/peano_lab/library/eisenstein_remainder_nonzero_candidate.py)
- Candidate source: [Eisenstein quotient bound](../../peano-lab/py/peano_lab/library/eisenstein_quotient_bound_candidate.py)
- Focused test: [Eisenstein quotient bound](../../peano-lab/py/tests/test_eisenstein_quotient_bound_candidate.py)
- Candidate source: [Eisenstein exact initial-segment count](../../peano-lab/py/peano_lab/library/eisenstein_initial_segment_count_candidate.py)
- Focused test: [Eisenstein exact initial-segment count](../../peano-lab/py/tests/test_eisenstein_initial_segment_count_candidate.py)
- Candidate source: [Exact beta-sum transport](../../peano-lab/py/peano_lab/library/finite_sum_transport_candidate.py)
- Focused test: [Exact beta-sum transport](../../peano-lab/py/tests/test_finite_sum_transport_candidate.py)
- Candidate source: [Exact pointwise beta-sum addition](../../peano-lab/py/peano_lab/library/finite_sum_pointwise_add_candidate.py)
- Focused test: [Exact pointwise beta-sum addition](../../peano-lab/py/tests/test_finite_sum_pointwise_add_candidate.py)
- Candidate source: [Exact constant-prefix sums](../../peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py)
- Focused test: [Exact constant-prefix sums](../../peano-lab/py/tests/test_finite_repeat_sum_candidate.py)
- Candidate source: [Complementary beta-bit counts](../../peano-lab/py/peano_lab/library/finite_bitcount_complement_candidate.py)
- Focused test: [Complementary beta-bit counts](../../peano-lab/py/tests/test_finite_bitcount_complement_candidate.py)
- Candidate source: [Eisenstein row-quotient bridge](../../peano-lab/py/peano_lab/library/eisenstein_row_quotient_candidate.py)
- Focused test: [Eisenstein row-quotient bridge](../../peano-lab/py/tests/test_eisenstein_row_quotient_candidate.py)
- Candidate source: [Eisenstein outer-sum bridge](../../peano-lab/py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py)
- Focused test: [Eisenstein outer-sum bridge](../../peano-lab/py/tests/test_eisenstein_outer_sum_bridge_candidate.py)
- Candidate source: [Eisenstein transposed cells](../../peano-lab/py/peano_lab/library/eisenstein_transposed_cell_candidate.py)
- Focused test: [Eisenstein transposed cells](../../peano-lab/py/tests/test_eisenstein_transposed_cell_candidate.py)
- Candidate source: [Eisenstein transposed outer cells](../../peano-lab/py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py)
- Focused test: [Eisenstein transposed outer cells](../../peano-lab/py/tests/test_eisenstein_transposed_outer_cell_candidate.py)
- Candidate source: [Eisenstein transposed columns](../../peano-lab/py/peano_lab/library/eisenstein_transposed_column_candidate.py)
- Focused test: [Eisenstein transposed columns](../../peano-lab/py/tests/test_eisenstein_transposed_column_candidate.py)
- Candidate source: [Gauss--Eisenstein pointwise alignment](../../peano-lab/py/peano_lab/library/gauss_eisenstein_pointwise_candidate.py)
- Candidate source: [Gauss--Eisenstein sum alignment](../../peano-lab/py/peano_lab/library/gauss_eisenstein_sum_candidate.py)
- Candidate source: [Two-prime data package](../../peano-lab/py/peano_lab/library/gauss_eisenstein_data_candidate.py)
- Candidate source: [Exact quadratic reciprocity](../../peano-lab/py/peano_lab/library/quadratic_reciprocity_candidate.py)

## Remaining trust and extension gates

1. admit the isolated arbitrary β-coded product-reindex candidates;
2. admit the eight-rung nonzero residue-product route and both Fermat
   endpoints;
3. discover and admit the bounded square-one classification and seven
   inverse-index/prefix candidates;
4. validate and admit the six extensional inverse-map, three explicit
   endpoint, two nonendpoint-orbit, two adjacent-pair-product, eight
   finite-omission, and nine PairOrder-extension candidates;
5. recursively validate and admit the now-body-green Wilson endpoint,
   including its separate coincident-prime-`2` branch;
6. recursively validate, mutate and admit the now body-green full Euler graph,
   including the five-body nonresidue endpoint, seven-body bounded-equivalence
   package, and six-body arbitrary-representative transport;
7. recursively validate and mutate the complete bounded/arbitrary Gauss graph,
   then admit it only through a separate pinned replay;
8. compile the complete body-green graph into the 45-package layered ordinary-
   `Cut` certificate, then validate and mutate that exact artifact with
   capacity, formula, RSS, independent-kernel, and browser checks;
9. admit the exact QR surface only after that replay, then derive the
   supplementary laws as separately scoped extensions.

## Trust and capacity

The live policy admits at most 500,000 structural occurrences, 100,000
distinct proof objects and depth 256. These availability limits do not change
the independent kernel or grant theorem authority. The FTA measurement gives
73,767 occurrences but only 8,701 distinct proof objects. Recursive QR closure
cannot pass: 191,669 theorem occurrences force at least 731,482 proof nodes.
The selected unchanged-kernel layered compiler uses 45 ordinary package Cuts;
its complete QR metrics and admission receipts remain pending.

## Project views

- Interactive proof graph: `book/_static/pa-proof-explorer/index.html`
- Permanent QR endpoint: `book/_static/pa-proof-explorer/tag/PA00FW.html`
- Explorer design: `research/arithmetic-library/pa-proof-explorer.md`
- Book chapter: `book/arithmetic-library/quadratic-reciprocity.md`
- Exact surface: `research/arithmetic-library/quadratic-reciprocity-surface.md`
- Finite folds: `research/arithmetic-library/finite-fold-surface.md`
- Capacity: `research/arithmetic-library/quadratic-reciprocity-capacity.md`
- Recursive hotspot audit: `research/arithmetic-library/quadratic-reciprocity-closure-hotspots.md`
- Layered unchanged-kernel closure: `research/arithmetic-library/layered-cut-bundle.md`
- Public admission path: `research/arithmetic-library/quadratic-reciprocity-admission-path.md`
- Closed-DAG fallback: `research/arithmetic-library/closed-proof-dag.md`
- Product reindexing: `research/arithmetic-library/product-permutation-invariance.md`
- PairOrder: `research/arithmetic-library/pair-order-encoding.md`
- Euler scaled inverse: `research/arithmetic-library/euler-scaled-inverse.md`
- Gauss magnitude permutation: `research/arithmetic-library/gauss-magnitude-permutation.md`
- Eisenstein division prefix: `research/arithmetic-library/eisenstein-division-prefix.md`
- Plan: `PLAN/11_quadratic_reciprocity.md`

## Up

[[arithmetic-library-moc]] · [[peano-lab-moc]] · [[00-index]]

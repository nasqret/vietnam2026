---
title: Foundational arithmetic library — Map of Content
tags: [moc, peano-arithmetic, number-theory, library]
---

> The executable and planned dependency graph from elementary equality through
> divisibility, modular arithmetic, primes, and unique factorization.

The current runtime contains 384 checked entries and the factorization tranche
is fully synchronized. The exact native sorted Gödel-β endpoints check from the
empty context: existence at 43,973 nodes/depth 98, canonical extensional
uniqueness at 29,789/depth 82, and combined
[[fundamental-theorem-of-arithmetic|FTA]] at 73,767 nodes/depth 99 with 2,184
self-contained Cuts.

The synchronized research catalog has 385 entries: 23 baseline checked, 361
post-baseline checked, and one representation-blocked conventional
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

The generated 384-theorem snapshot has 1,806,923 structural occurrences,
52,626 Cuts, and ordered
root
`73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b`.
The synchronized vault includes all 384 generated theorem notes.

## Design and trust

- [[quadratic-reciprocity-moc]]
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

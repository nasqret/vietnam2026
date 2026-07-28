---
title: Foundational arithmetic library — Map of Content
tags: [moc, peano-arithmetic, number-theory, library]
---

> The executable and planned dependency graph from elementary equality through
> divisibility, modular arithmetic, primes, and unique factorization.

The current runtime has 125 unique checked nodes: 23 from the original ladder
and 102 in the reconciled post-baseline extension. Of the latter, 90 form the
general foundational layer and twelve form the fixed modular capstone. The
broader 138-node catalog contains nine `planned_expressible` and four
`blocked_by_language` nodes in addition to those checked layers. One
separately cataloged Lean companion checks full list-based FTA existence and
uniqueness; it is not counted as a Peano theorem.

## Design and trust

- [[foundational-arithmetic-library]]
- [[lemma-dependency-dag]]
- [[arithmetic-library-provenance]]
- [[theorem-ladder]]
- [[trusted-kernel]]
- [[proof-certificate]]

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
- [[multiple_trans]] · [[multiple_antisymm]]
- [[divisor_le_nonzero]] · [[divisor_one]]
- [[factor_difference]] · [[divides_remainder]] · [[divides_linear_step]]
- [[not_multiple_pointwise]] · [[not_multiple_from_pointwise]]

## Checked gcd and coprimality API

- [[is_gcd_symm]] · [[is_gcd_dvd_left]] · [[is_gcd_dvd_right]]
- [[is_gcd_greatest]] · [[is_gcd_of_dvd]] · [[is_gcd_unique]]
- [[is_gcd_zero_right]] · [[is_gcd_euclid_forward]] · [[is_gcd_euclid_backward]]
- [[coprime_symm]] · [[coprime_one_left]] · [[coprime_one_right]]
- [[coprime_to_is_gcd_one]] · [[is_gcd_one_to_coprime]]

## Checked quotient-and-remainder algebra

- [[division_remainder_succ]] · [[division_remainder_exists]] · [[division_remainder_unique]]
- [[remainder_bound_step]] · [[division_block_upper]] · [[positive_quotient_gap_impossible]]
- [[zero_remainder_implies_multiple]] · [[multiple_has_zero_remainder]]
- [[add_residue]] · [[add_residue_lift]]
- [[square_decomp]] · [[square_residue_lift]] · [[square_residue_witness]]

## Checked first prime instance

- [[prime_two]] — the fully expanded factor-pair predicate for the numeral two

## Executable and documentary views

- Runtime: `peano-lab/py/peano_lab/library/theorems.py`
- Catalog: `research/arithmetic-library/catalog.json`
- Generated snapshot: `artifacts/peano-library/catalog-v1.json`
- Dependency graph: `artifacts/peano-library/dependency-graph.mmd`
- Book: `book/arithmetic-library/`
- Plan: `PLAN/10_arithmetic_library.md`

## Up

[[peano-lab-moc]] · [[00-index]]

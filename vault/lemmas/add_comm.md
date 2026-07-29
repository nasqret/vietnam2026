---
title: "Lemma: add_comm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_comm`

Addition is commutative.

## Closed Peano statement

```text
forall n m. n + m = m + n
```

## Dependencies

- [[zero_add]]
- [[add_succ_left]]

## Checked dependents

- [[mul_succ_left]]
- [[add_left_cancel]]
- [[le_add_right]]
- [[add_le_add_left]]
- [[mul_lt_mul_succ_left_nonzero]]
- [[division_block_upper]]
- [[positive_quotient_gap_impossible]]
- [[add_eq_zero_left]]
- [[factor_difference]]
- [[add_permute_outer]]
- [[balanced_bezout_euclid_step]]
- [[common_divisor_divides_balanced_result]]
- [[mod_eq_trans]]
- [[mod_eq_add]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_bounded_unique]]
- [[mod_eq_to_remainder_decomposition]]
- [[add_residue_lift]]
- [[bezout_mod_left]]
- [[mod_eq_predecessor_cancel]]
- [[beta_moduli_coprime_of_lt_bounded_common_multiple]]
- [[prime_unbounded]]
- [[mod5_square_residue_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **73 nodes**, depth **12**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib add_comm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

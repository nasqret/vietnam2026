---
title: "Lemma: mul_comm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_comm`

Multiplication is commutative.

## Closed Peano statement

```text
forall n m. n * m = m * n
```

## Dependencies

- [[mul_zero_left]]
- [[mul_succ_left]]

## Checked dependents

- [[add_mul]]
- [[mul_right_cancel_nonzero]]
- [[multiple_mul_left]]
- [[balanced_combination_scale_right]]
- [[mod_eq_mul_left]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_to_remainder_decomposition]]
- [[beta_at_exists]]
- [[beta_at_unique]]
- [[square_decomp]]
- [[binary_crt]]
- [[beta_modulus_coprime_base]]
- [[beta_moduli_coprime_of_gap_dvd]]
- [[bounded_common_multiple_step]]
- [[right_factor_divides_product]]
- [[greatest_prime_divisor_quotient_bound]]
- [[greatest_prime_divisor_descent]]
- [[beta_factor_divides_product]]
- [[prime_factorization_exists_up_to]]
- [[two_prime_product_uniqueness]]

## Verification record

- Independently checked from the empty context.
- Certificate: **222 nodes**, depth **24**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib mul_comm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

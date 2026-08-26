---
title: "Lemma: mul_add"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_add`

Multiplication distributes over addition on the right.

## Closed Peano statement

```text
forall n m k. n * (m + k) = n * m + n * k
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- [[mul_assoc]]
- [[add_mul]]
- [[mul_le_mul_left]]
- [[positive_quotient_gap_impossible]]
- [[multiple_add]]
- [[divides_linear_step]]
- [[balanced_bezout_euclid_step]]
- [[common_divisor_divides_balanced_result]]
- [[mod_eq_trans]]
- [[mod_eq_add]]
- [[add_residue]]
- [[add_residue_lift]]
- [[square_decomp]]
- [[binary_crt]]
- [[mod5_square_residue_one]]
- [[mod5_square_residue_two]]
- [[even_add_even]]
- [[even_add_odd]]
- [[odd_add_even]]
- [[odd_add_odd]]
- [[odd_mul_odd]]
- [[odd_mod4_cases]]
- [[mod4_three_is_odd]]
- [[coprime_mod_inverse]]
- [[balanced_bezout_cancel_gcd]]
- [[mod_eq_scale]]

## Verification record

- Independently checked from the empty context.
- Certificate: **77 nodes**, depth **16**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib mul_add`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

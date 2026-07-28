---
title: "Lemma: add_mul"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_mul`

Multiplication distributes over addition on the left.

## Closed Peano statement

```text
forall n m k. (n + m) * k = n * k + m * k
```

## Dependencies

- [[mul_comm]]
- [[mul_add]]

## Checked dependents

- [[mul_le_mul_right]]
- [[balanced_bezout_euclid_step]]
- [[balanced_combination_scale_right]]
- [[mod_eq_mul_right]]
- [[square_decomp]]
- [[common_divisor_beta_moduli_divides_gap_times_c]]

## Verification record

- Independently checked from the empty context.
- Certificate: **326 nodes**, depth **25**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib add_mul`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

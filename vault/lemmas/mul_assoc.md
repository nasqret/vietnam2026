---
title: "Lemma: mul_assoc"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_assoc`

Multiplication is associative.

## Closed Peano statement

```text
forall n m k. (n * m) * k = n * (m * k)
```

## Dependencies

- [[mul_add]]

## Checked dependents

- [[multiple_mul_right]]
- [[multiple_trans]]
- [[multiple_antisymm]]
- [[divides_remainder]]
- [[divides_linear_step]]
- [[balanced_bezout_euclid_step]]
- [[balanced_combination_scale_right]]
- [[common_divisor_divides_balanced_result]]
- [[mod_eq_mul_right]]
- [[square_decomp]]
- [[binary_crt]]
- [[mod_eq_of_mod_eq_multiple]]
- [[fourth_power_regroup]]
- [[mod5_square_residue_one]]
- [[mod5_square_residue_two]]
- [[mod5_fourth_power_residue_one]]
- [[mod5_fourth_power_residue_two]]
- [[mod5_fourth_power_residue_three]]
- [[mod5_fourth_power_residue_four]]
- [[mod5_fourth_power_one]]

## Verification record

- Independently checked from the empty context.
- Certificate: **116 nodes**, depth **17**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib mul_assoc`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

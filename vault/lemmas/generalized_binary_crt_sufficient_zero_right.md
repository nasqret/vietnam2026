---
title: "Lemma: generalized_binary_crt_sufficient_zero_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_sufficient_zero_right`

If the right modulus is zero, gcd compatibility constructs a solution by choosing the right residue.

## Closed Peano statement

```text
forall g m a b. ((((exists hage_left_factor_zero_right_gcd. m = g * hage_left_factor_zero_right_gcd) /\ (exists hage_right_factor_zero_right_gcd. 0 = g * hage_right_factor_zero_right_gcd)) /\ forall hage_divisor_zero_right_gcd. (exists hage_common_left_zero_right_gcd. m = hage_divisor_zero_right_gcd * hage_common_left_zero_right_gcd) -> (exists hage_common_right_zero_right_gcd. 0 = hage_divisor_zero_right_gcd * hage_common_right_zero_right_gcd) -> exists hage_greatest_factor_zero_right_gcd. g = hage_divisor_zero_right_gcd * hage_greatest_factor_zero_right_gcd)) -> (exists hgcrt_mod_left_zero_right_compatibility hgcrt_mod_right_zero_right_compatibility. a + g * hgcrt_mod_left_zero_right_compatibility = b + g * hgcrt_mod_right_zero_right_compatibility) -> exists x. (((exists hgcrt_mod_left_zero_right_solution_left hgcrt_mod_right_zero_right_solution_left. x + m * hgcrt_mod_left_zero_right_solution_left = a + m * hgcrt_mod_right_zero_right_solution_left) /\ (exists hgcrt_mod_left_zero_right_solution_right hgcrt_mod_right_zero_right_solution_right. x + 0 * hgcrt_mod_left_zero_right_solution_right = b + 0 * hgcrt_mod_right_zero_right_solution_right)))
```

## Dependencies

- [[is_gcd_zero_right]]
- [[is_gcd_unique]]
- [[mod_eq_symm]]
- [[mod_eq_refl]]

## Checked dependents

- [[generalized_binary_crt_sufficient]]

## Verification record

- Independently checked from the empty context.
- Certificate: **805 nodes**, depth **36**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib generalized_binary_crt_sufficient_zero_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

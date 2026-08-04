---
title: "Lemma: generalized_binary_crt_sufficient_zero_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_sufficient_zero_left`

If the left modulus is zero, gcd compatibility constructs a solution by choosing the left residue.

## Closed Peano statement

```text
forall g n a b. ((((exists hage_left_factor_zero_left_gcd. 0 = g * hage_left_factor_zero_left_gcd) /\ (exists hage_right_factor_zero_left_gcd. n = g * hage_right_factor_zero_left_gcd)) /\ forall hage_divisor_zero_left_gcd. (exists hage_common_left_zero_left_gcd. 0 = hage_divisor_zero_left_gcd * hage_common_left_zero_left_gcd) -> (exists hage_common_right_zero_left_gcd. n = hage_divisor_zero_left_gcd * hage_common_right_zero_left_gcd) -> exists hage_greatest_factor_zero_left_gcd. g = hage_divisor_zero_left_gcd * hage_greatest_factor_zero_left_gcd)) -> (exists hgcrt_mod_left_zero_left_compatibility hgcrt_mod_right_zero_left_compatibility. a + g * hgcrt_mod_left_zero_left_compatibility = b + g * hgcrt_mod_right_zero_left_compatibility) -> exists x. (((exists hgcrt_mod_left_zero_left_solution_left hgcrt_mod_right_zero_left_solution_left. x + 0 * hgcrt_mod_left_zero_left_solution_left = a + 0 * hgcrt_mod_right_zero_left_solution_left) /\ (exists hgcrt_mod_left_zero_left_solution_right hgcrt_mod_right_zero_left_solution_right. x + n * hgcrt_mod_left_zero_left_solution_right = b + n * hgcrt_mod_right_zero_left_solution_right)))
```

## Dependencies

- [[is_gcd_symm]]
- [[is_gcd_zero_right]]
- [[is_gcd_unique]]
- [[mod_eq_refl]]

## Checked dependents

- [[generalized_binary_crt_sufficient]]

## Verification record

- Independently checked from the empty context.
- Certificate: **834 nodes**, depth **37**.
- Authored script length: **31 commands**.
- Runtime card: `pa lib generalized_binary_crt_sufficient_zero_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

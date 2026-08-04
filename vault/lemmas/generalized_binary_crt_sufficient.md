---
title: "Lemma: generalized_binary_crt_sufficient"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_sufficient`

Gcd compatibility constructs a common solution for arbitrary natural moduli, including zero.

## Closed Peano statement

```text
forall g m n a b. ((((exists hag_left_factor_total_sufficiency_gcd. m = g * hag_left_factor_total_sufficiency_gcd) /\ (exists hag_right_factor_total_sufficiency_gcd. n = g * hag_right_factor_total_sufficiency_gcd)) /\ forall hag_divisor_total_sufficiency_gcd. (exists hag_common_left_total_sufficiency_gcd. m = hag_divisor_total_sufficiency_gcd * hag_common_left_total_sufficiency_gcd) -> (exists hag_common_right_total_sufficiency_gcd. n = hag_divisor_total_sufficiency_gcd * hag_common_right_total_sufficiency_gcd) -> exists hag_greatest_factor_total_sufficiency_gcd. g = hag_divisor_total_sufficiency_gcd * hag_greatest_factor_total_sufficiency_gcd)) -> (exists hgcrt_mod_left_total_sufficiency_compatibility hgcrt_mod_right_total_sufficiency_compatibility. a + g * hgcrt_mod_left_total_sufficiency_compatibility = b + g * hgcrt_mod_right_total_sufficiency_compatibility) -> exists x. (((exists hgcrt_mod_left_total_sufficiency_solution_left hgcrt_mod_right_total_sufficiency_solution_left. x + m * hgcrt_mod_left_total_sufficiency_solution_left = a + m * hgcrt_mod_right_total_sufficiency_solution_left) /\ (exists hgcrt_mod_left_total_sufficiency_solution_right hgcrt_mod_right_total_sufficiency_solution_right. x + n * hgcrt_mod_left_total_sufficiency_solution_right = b + n * hgcrt_mod_right_total_sufficiency_solution_right)))
```

## Dependencies

- [[eq_decidable]]
- [[generalized_binary_crt_sufficient_zero_left]]
- [[generalized_binary_crt_sufficient_zero_right]]
- [[generalized_binary_crt_sufficient_nonzero]]

## Checked dependents

- [[generalized_binary_crt_solvable_iff]]
- [[generalized_binary_crt_canonical_boundary]]
- [[generalized_binary_crt_solution_or_obstruction]]

## Verification record

- Independently checked from the empty context.
- Certificate: **11240 nodes**, depth **78**.
- Authored script length: **49 commands**.
- Runtime card: `pa lib generalized_binary_crt_sufficient`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

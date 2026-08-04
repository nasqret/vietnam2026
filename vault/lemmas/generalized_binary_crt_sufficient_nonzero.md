---
title: "Lemma: generalized_binary_crt_sufficient_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_sufficient_nonzero`

Gcd compatibility is sufficient for a common solution when both moduli are nonzero.

## Closed Peano statement

```text
forall g m n a b. ~(m = 0) -> ~(n = 0) -> ((((exists hag_left_factor_sufficient_assumption. m = g * hag_left_factor_sufficient_assumption) /\ (exists hag_right_factor_sufficient_assumption. n = g * hag_right_factor_sufficient_assumption)) /\ forall hag_divisor_sufficient_assumption. (exists hag_common_left_sufficient_assumption. m = hag_divisor_sufficient_assumption * hag_common_left_sufficient_assumption) -> (exists hag_common_right_sufficient_assumption. n = hag_divisor_sufficient_assumption * hag_common_right_sufficient_assumption) -> exists hag_greatest_factor_sufficient_assumption. g = hag_divisor_sufficient_assumption * hag_greatest_factor_sufficient_assumption)) -> (exists hgcrt_mod_left_sufficient_compatibility hgcrt_mod_right_sufficient_compatibility. a + g * hgcrt_mod_left_sufficient_compatibility = b + g * hgcrt_mod_right_sufficient_compatibility) -> exists x. (((exists hgcrt_mod_left_sufficient_result_left hgcrt_mod_right_sufficient_result_left. x + m * hgcrt_mod_left_sufficient_result_left = a + m * hgcrt_mod_right_sufficient_result_left) /\ (exists hgcrt_mod_left_sufficient_result_right hgcrt_mod_right_sufficient_result_right. x + n * hgcrt_mod_left_sufficient_result_right = b + n * hgcrt_mod_right_sufficient_result_right)))
```

## Dependencies

- [[is_gcd_dvd_left]]
- [[is_gcd_dvd_right]]
- [[mul_zero_left]]
- [[is_gcd_quotients_coprime_nonzero]]
- [[mod_eq_common_remainder_decomposition]]
- [[crt_scaled_common_remainder_lift]]

## Checked dependents

- [[generalized_binary_crt_sufficient]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9482 nodes**, depth **74**.
- Authored script length: **85 commands**.
- Runtime card: `pa lib generalized_binary_crt_sufficient_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

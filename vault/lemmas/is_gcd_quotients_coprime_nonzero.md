---
title: "Lemma: is_gcd_quotients_coprime_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_quotients_coprime_nonzero`

Nonzero gcd cofactors are coprime by the greatest-divisor property.

## Closed Peano statement

```text
forall g m n M N. ((((exists hag_left_factor_quotient_assumption. m = g * hag_left_factor_quotient_assumption) /\ (exists hag_right_factor_quotient_assumption. n = g * hag_right_factor_quotient_assumption)) /\ forall hag_divisor_quotient_assumption. (exists hag_common_left_quotient_assumption. m = hag_divisor_quotient_assumption * hag_common_left_quotient_assumption) -> (exists hag_common_right_quotient_assumption. n = hag_divisor_quotient_assumption * hag_common_right_quotient_assumption) -> exists hag_greatest_factor_quotient_assumption. g = hag_divisor_quotient_assumption * hag_greatest_factor_quotient_assumption)) -> ~(g = 0) -> m = g * M -> n = g * N -> (forall hmi_divisor_quotient_result. (exists hmi_left_factor_quotient_result. M = hmi_divisor_quotient_result * hmi_left_factor_quotient_result) -> (exists hmi_right_factor_quotient_result. N = hmi_divisor_quotient_result * hmi_right_factor_quotient_result) -> hmi_divisor_quotient_result = 1)
```

## Dependencies

- [[is_gcd_greatest]]
- [[mul_assoc]]
- [[mul_one]]
- [[mul_left_cancel_nonzero]]
- [[divisor_one]]

## Checked dependents

- [[generalized_binary_crt_sufficient_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **660 nodes**, depth **33**.
- Authored script length: **61 commands**.
- Runtime card: `pa lib is_gcd_quotients_coprime_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

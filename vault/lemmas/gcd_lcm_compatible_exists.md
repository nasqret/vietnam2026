---
title: "Lemma: gcd_lcm_compatible_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_lcm_compatible_exists`

Every pair has compatible relational gcd and lcm witnesses whose product is the product of the inputs, including zero inputs.

## Closed Peano statement

```text
forall a b. exists g l. ((((((exists hag_left_factor_compatible. a = g * hag_left_factor_compatible) /\ (exists hag_right_factor_compatible. b = g * hag_right_factor_compatible)) /\ forall hag_divisor_compatible. (exists hag_common_left_compatible. a = hag_divisor_compatible * hag_common_left_compatible) -> (exists hag_common_right_compatible. b = hag_divisor_compatible * hag_common_right_compatible) -> exists hag_greatest_factor_compatible. g = hag_divisor_compatible * hag_greatest_factor_compatible)) /\ ((((exists hlcm_left_factor_compatible. l = a * hlcm_left_factor_compatible) /\ (exists hlcm_right_factor_compatible. l = b * hlcm_right_factor_compatible)) /\ forall hlcm_common_compatible. (exists hlcm_left_common_compatible. hlcm_common_compatible = a * hlcm_left_common_compatible) -> (exists hlcm_right_common_compatible. hlcm_common_compatible = b * hlcm_right_common_compatible) -> exists hlcm_least_factor_compatible. hlcm_common_compatible = l * hlcm_least_factor_compatible))) /\ g * l = a * b)
```

## Dependencies

- [[gcd_balanced_bezout_exists]]
- [[eq_decidable]]
- [[gcd_zero_inputs]]
- [[is_lcm_zero_left]]
- [[balanced_bezout_cancel_gcd]]
- [[balanced_bezout_one_implies_coprime]]
- [[coprime_product_is_lcm]]
- [[is_lcm_scale_nonzero]]
- [[mul_assoc]]
- [[mul_comm]]

## Checked dependents

- [[lcm_exists_relational]]
- [[gcd_lcm_product]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9038 nodes**, depth **60**.
- Authored script length: **108 commands**.
- Runtime card: `pa lib gcd_lcm_compatible_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

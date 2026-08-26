---
title: "Lemma: coprime_product_is_lcm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_product_is_lcm`

The product of coprime naturals satisfies the universal relational LCM specification.

## Closed Peano statement

```text
forall a b. (forall d. (exists u. a = d * u) -> (exists v. b = d * v) -> d = 1) -> ((((exists hlcm_left_factor_coprime_product. a * b = a * hlcm_left_factor_coprime_product) /\ (exists hlcm_right_factor_coprime_product. a * b = b * hlcm_right_factor_coprime_product)) /\ forall hlcm_common_coprime_product. (exists hlcm_left_common_coprime_product. hlcm_common_coprime_product = a * hlcm_left_common_coprime_product) -> (exists hlcm_right_common_coprime_product. hlcm_common_coprime_product = b * hlcm_right_common_coprime_product) -> exists hlcm_least_factor_coprime_product. hlcm_common_coprime_product = a * b * hlcm_least_factor_coprime_product))
```

## Dependencies

- [[mul_comm]]
- [[gauss_coprime_cancel]]
- [[mul_assoc]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4191 nodes**, depth **53**.
- Authored script length: **40 commands**.
- Runtime card: `pa lib coprime_product_is_lcm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

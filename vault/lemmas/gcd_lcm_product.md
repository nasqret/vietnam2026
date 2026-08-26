---
title: "Lemma: gcd_lcm_product"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_lcm_product`

Any relational gcd and LCM pair satisfies the gcd--LCM product identity, by uniqueness from a compatible pair.

## Closed Peano statement

```text
forall g l a b. ((((exists hag_left_factor_product_gcd_assumption. a = g * hag_left_factor_product_gcd_assumption) /\ (exists hag_right_factor_product_gcd_assumption. b = g * hag_right_factor_product_gcd_assumption)) /\ forall hag_divisor_product_gcd_assumption. (exists hag_common_left_product_gcd_assumption. a = hag_divisor_product_gcd_assumption * hag_common_left_product_gcd_assumption) -> (exists hag_common_right_product_gcd_assumption. b = hag_divisor_product_gcd_assumption * hag_common_right_product_gcd_assumption) -> exists hag_greatest_factor_product_gcd_assumption. g = hag_divisor_product_gcd_assumption * hag_greatest_factor_product_gcd_assumption)) -> ((((exists hlcm_left_factor_product_lcm_assumption. l = a * hlcm_left_factor_product_lcm_assumption) /\ (exists hlcm_right_factor_product_lcm_assumption. l = b * hlcm_right_factor_product_lcm_assumption)) /\ forall hlcm_common_product_lcm_assumption. (exists hlcm_left_common_product_lcm_assumption. hlcm_common_product_lcm_assumption = a * hlcm_left_common_product_lcm_assumption) -> (exists hlcm_right_common_product_lcm_assumption. hlcm_common_product_lcm_assumption = b * hlcm_right_common_product_lcm_assumption) -> exists hlcm_least_factor_product_lcm_assumption. hlcm_common_product_lcm_assumption = l * hlcm_least_factor_product_lcm_assumption)) -> g * l = a * b
```

## Dependencies

- [[gcd_lcm_compatible_exists]]
- [[is_gcd_unique]]
- [[is_lcm_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **10441 nodes**, depth **61**.
- Authored script length: **31 commands**.
- Runtime card: `pa lib gcd_lcm_product`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

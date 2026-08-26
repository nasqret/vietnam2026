---
title: "Lemma: is_lcm_zero_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_zero_right`

Zero is an lcm of every natural and zero.

## Closed Peano statement

```text
forall a. ((((exists hlcm_left_factor_zero_right. 0 = a * hlcm_left_factor_zero_right) /\ (exists hlcm_right_factor_zero_right. 0 = 0 * hlcm_right_factor_zero_right)) /\ forall hlcm_common_zero_right. (exists hlcm_left_common_zero_right. hlcm_common_zero_right = a * hlcm_left_common_zero_right) -> (exists hlcm_right_common_zero_right. hlcm_common_zero_right = 0 * hlcm_right_common_zero_right) -> exists hlcm_least_factor_zero_right. hlcm_common_zero_right = 0 * hlcm_least_factor_zero_right))
```

## Dependencies

- [[multiple_zero]]

## Checked dependents

- [[is_lcm_zero_left]]

## Verification record

- Independently checked from the empty context.
- Certificate: **25 nodes**, depth **7**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib is_lcm_zero_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

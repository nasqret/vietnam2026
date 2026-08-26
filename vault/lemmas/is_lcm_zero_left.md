---
title: "Lemma: is_lcm_zero_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_zero_left`

Zero is an lcm of zero and every natural.

## Closed Peano statement

```text
forall b. ((((exists hlcm_left_factor_zero_left. 0 = 0 * hlcm_left_factor_zero_left) /\ (exists hlcm_right_factor_zero_left. 0 = b * hlcm_right_factor_zero_left)) /\ forall hlcm_common_zero_left. (exists hlcm_left_common_zero_left. hlcm_common_zero_left = 0 * hlcm_left_common_zero_left) -> (exists hlcm_right_common_zero_left. hlcm_common_zero_left = b * hlcm_right_common_zero_left) -> exists hlcm_least_factor_zero_left. hlcm_common_zero_left = 0 * hlcm_least_factor_zero_left))
```

## Dependencies

- [[is_lcm_zero_right]]
- [[is_lcm_symm]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **71 nodes**, depth **23**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib is_lcm_zero_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

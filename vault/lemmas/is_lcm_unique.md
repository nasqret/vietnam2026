---
title: "Lemma: is_lcm_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_unique`

The expanded relational lcm specification is single-valued.

## Closed Peano statement

```text
forall l m a b. ((((exists hlcm_left_factor_unique_left. l = a * hlcm_left_factor_unique_left) /\ (exists hlcm_right_factor_unique_left. l = b * hlcm_right_factor_unique_left)) /\ forall hlcm_common_unique_left. (exists hlcm_left_common_unique_left. hlcm_common_unique_left = a * hlcm_left_common_unique_left) -> (exists hlcm_right_common_unique_left. hlcm_common_unique_left = b * hlcm_right_common_unique_left) -> exists hlcm_least_factor_unique_left. hlcm_common_unique_left = l * hlcm_least_factor_unique_left)) -> ((((exists hlcm_left_factor_unique_right. m = a * hlcm_left_factor_unique_right) /\ (exists hlcm_right_factor_unique_right. m = b * hlcm_right_factor_unique_right)) /\ forall hlcm_common_unique_right. (exists hlcm_left_common_unique_right. hlcm_common_unique_right = a * hlcm_left_common_unique_right) -> (exists hlcm_right_common_unique_right. hlcm_common_unique_right = b * hlcm_right_common_unique_right) -> exists hlcm_least_factor_unique_right. hlcm_common_unique_right = m * hlcm_least_factor_unique_right)) -> l = m
```

## Dependencies

- [[multiple_antisymm]]

## Checked dependents

- [[canonical_lcm_exists_unique]]
- [[gcd_lcm_product]]

## Verification record

- Independently checked from the empty context.
- Certificate: **680 nodes**, depth **34**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib is_lcm_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

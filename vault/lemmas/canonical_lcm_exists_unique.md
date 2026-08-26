---
title: "Lemma: canonical_lcm_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_lcm_exists_unique`

The relational LCM value exists uniquely; divisibility witnesses themselves are not claimed to be unique.

## Closed Peano statement

```text
forall a b. exists l. (((((exists hlcm_left_factor_unique_chosen. l = a * hlcm_left_factor_unique_chosen) /\ (exists hlcm_right_factor_unique_chosen. l = b * hlcm_right_factor_unique_chosen)) /\ forall hlcm_common_unique_chosen. (exists hlcm_left_common_unique_chosen. hlcm_common_unique_chosen = a * hlcm_left_common_unique_chosen) -> (exists hlcm_right_common_unique_chosen. hlcm_common_unique_chosen = b * hlcm_right_common_unique_chosen) -> exists hlcm_least_factor_unique_chosen. hlcm_common_unique_chosen = l * hlcm_least_factor_unique_chosen)) /\ forall m. ((((exists hlcm_left_factor_unique_compared. m = a * hlcm_left_factor_unique_compared) /\ (exists hlcm_right_factor_unique_compared. m = b * hlcm_right_factor_unique_compared)) /\ forall hlcm_common_unique_compared. (exists hlcm_left_common_unique_compared. hlcm_common_unique_compared = a * hlcm_left_common_unique_compared) -> (exists hlcm_right_common_unique_compared. hlcm_common_unique_compared = b * hlcm_right_common_unique_compared) -> exists hlcm_least_factor_unique_compared. hlcm_common_unique_compared = m * hlcm_least_factor_unique_compared)) -> m = l)
```

## Dependencies

- [[lcm_exists_relational]]
- [[is_lcm_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **9791 nodes**, depth **62**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib canonical_lcm_exists_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

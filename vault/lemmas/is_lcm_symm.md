---
title: "Lemma: is_lcm_symm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_symm`

The expanded relational lcm specification is symmetric.

## Closed Peano statement

```text
forall l a b. ((((exists hlcm_left_factor_symmetry_source. l = a * hlcm_left_factor_symmetry_source) /\ (exists hlcm_right_factor_symmetry_source. l = b * hlcm_right_factor_symmetry_source)) /\ forall hlcm_common_symmetry_source. (exists hlcm_left_common_symmetry_source. hlcm_common_symmetry_source = a * hlcm_left_common_symmetry_source) -> (exists hlcm_right_common_symmetry_source. hlcm_common_symmetry_source = b * hlcm_right_common_symmetry_source) -> exists hlcm_least_factor_symmetry_source. hlcm_common_symmetry_source = l * hlcm_least_factor_symmetry_source)) -> ((((exists hlcm_left_factor_symmetry_target. l = b * hlcm_left_factor_symmetry_target) /\ (exists hlcm_right_factor_symmetry_target. l = a * hlcm_right_factor_symmetry_target)) /\ forall hlcm_common_symmetry_target. (exists hlcm_left_common_symmetry_target. hlcm_common_symmetry_target = b * hlcm_left_common_symmetry_target) -> (exists hlcm_right_common_symmetry_target. hlcm_common_symmetry_target = a * hlcm_right_common_symmetry_target) -> exists hlcm_least_factor_symmetry_target. hlcm_common_symmetry_target = l * hlcm_least_factor_symmetry_target))
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[is_lcm_zero_left]]

## Verification record

- Independently checked from the empty context.
- Certificate: **36 nodes**, depth **21**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib is_lcm_symm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

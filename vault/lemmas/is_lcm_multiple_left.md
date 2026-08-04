---
title: "Lemma: is_lcm_multiple_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_multiple_left`

A relational lcm is a multiple of its left input.

## Closed Peano statement

```text
forall l a b. ((((exists hlcm_left_factor_projection_left. l = a * hlcm_left_factor_projection_left) /\ (exists hlcm_right_factor_projection_left. l = b * hlcm_right_factor_projection_left)) /\ forall hlcm_common_projection_left. (exists hlcm_left_common_projection_left. hlcm_common_projection_left = a * hlcm_left_common_projection_left) -> (exists hlcm_right_common_projection_left. hlcm_common_projection_left = b * hlcm_right_common_projection_left) -> exists hlcm_least_factor_projection_left. hlcm_common_projection_left = l * hlcm_least_factor_projection_left)) -> exists x. l = a * x
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mod_eq_lcm_iff_pair]]

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **13**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib is_lcm_multiple_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

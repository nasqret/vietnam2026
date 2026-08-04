---
title: "Lemma: is_lcm_multiple_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_multiple_right`

A relational lcm is a multiple of its right input.

## Closed Peano statement

```text
forall l a b. ((((exists hlcm_left_factor_projection_right. l = a * hlcm_left_factor_projection_right) /\ (exists hlcm_right_factor_projection_right. l = b * hlcm_right_factor_projection_right)) /\ forall hlcm_common_projection_right. (exists hlcm_left_common_projection_right. hlcm_common_projection_right = a * hlcm_left_common_projection_right) -> (exists hlcm_right_common_projection_right. hlcm_common_projection_right = b * hlcm_right_common_projection_right) -> exists hlcm_least_factor_projection_right. hlcm_common_projection_right = l * hlcm_least_factor_projection_right)) -> exists x. l = b * x
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **13**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib is_lcm_multiple_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

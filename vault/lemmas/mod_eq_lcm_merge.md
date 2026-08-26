---
title: "Lemma: mod_eq_lcm_merge"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_lcm_merge`

Congruence modulo both inputs merges to congruence modulo a relational lcm.

## Closed Peano statement

```text
forall l m n x y. ((((exists hlcm_left_factor_merge. l = m * hlcm_left_factor_merge) /\ (exists hlcm_right_factor_merge. l = n * hlcm_right_factor_merge)) /\ forall hlcm_common_merge. (exists hlcm_left_common_merge. hlcm_common_merge = m * hlcm_left_common_merge) -> (exists hlcm_right_common_merge. hlcm_common_merge = n * hlcm_right_common_merge) -> exists hlcm_least_factor_merge. hlcm_common_merge = l * hlcm_least_factor_merge)) -> (exists hgcrt_mod_left_merge_m hgcrt_mod_right_merge_m. x + m * hgcrt_mod_left_merge_m = y + m * hgcrt_mod_right_merge_m) -> (exists hgcrt_mod_left_merge_n hgcrt_mod_right_merge_n. x + n * hgcrt_mod_left_merge_n = y + n * hgcrt_mod_right_merge_n) -> (exists hgcrt_mod_left_merge_l hgcrt_mod_right_merge_l. x + l * hgcrt_mod_left_merge_l = y + l * hgcrt_mod_right_merge_l)
```

## Dependencies

- [[le_total]]
- [[mod_eq_symm]]
- [[mod_eq_ordered_gap_multiple]]
- [[is_lcm_least]]
- [[mul_comm]]
- [[remainder_decomposition_to_mod_eq]]

## Checked dependents

- [[mod_eq_lcm_iff_pair]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1315 nodes**, depth **33**.
- Authored script length: **113 commands**.
- Runtime card: `pa lib mod_eq_lcm_merge`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

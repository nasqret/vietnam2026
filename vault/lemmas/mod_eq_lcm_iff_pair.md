---
title: "Lemma: mod_eq_lcm_iff_pair"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_lcm_iff_pair`

Congruence modulo a relational lcm is equivalent to congruence modulo both inputs.

## Closed Peano statement

```text
forall l m n x y. ((((exists hlcm_left_factor_iff_pair. l = m * hlcm_left_factor_iff_pair) /\ (exists hlcm_right_factor_iff_pair. l = n * hlcm_right_factor_iff_pair)) /\ forall hlcm_common_iff_pair. (exists hlcm_left_common_iff_pair. hlcm_common_iff_pair = m * hlcm_left_common_iff_pair) -> (exists hlcm_right_common_iff_pair. hlcm_common_iff_pair = n * hlcm_right_common_iff_pair) -> exists hlcm_least_factor_iff_pair. hlcm_common_iff_pair = l * hlcm_least_factor_iff_pair)) -> (((exists hgcrt_mod_left_iff_l_forward hgcrt_mod_right_iff_l_forward. x + l * hgcrt_mod_left_iff_l_forward = y + l * hgcrt_mod_right_iff_l_forward) -> ((exists hgcrt_mod_left_iff_m_forward hgcrt_mod_right_iff_m_forward. x + m * hgcrt_mod_left_iff_m_forward = y + m * hgcrt_mod_right_iff_m_forward) /\ (exists hgcrt_mod_left_iff_n_forward hgcrt_mod_right_iff_n_forward. x + n * hgcrt_mod_left_iff_n_forward = y + n * hgcrt_mod_right_iff_n_forward))) /\ (((exists hgcrt_mod_left_iff_m_reverse hgcrt_mod_right_iff_m_reverse. x + m * hgcrt_mod_left_iff_m_reverse = y + m * hgcrt_mod_right_iff_m_reverse) /\ (exists hgcrt_mod_left_iff_n_reverse hgcrt_mod_right_iff_n_reverse. x + n * hgcrt_mod_left_iff_n_reverse = y + n * hgcrt_mod_right_iff_n_reverse)) -> (exists hgcrt_mod_left_iff_l_reverse hgcrt_mod_right_iff_l_reverse. x + l * hgcrt_mod_left_iff_l_reverse = y + l * hgcrt_mod_right_iff_l_reverse)))
```

## Dependencies

- [[is_lcm_multiple_left]]
- [[is_lcm_multiple_right]]
- [[mod_eq_of_mod_eq_multiple]]
- [[mod_eq_lcm_merge]]

## Checked dependents

- [[crt_solution_class_iff_lcm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1570 nodes**, depth **37**.
- Authored script length: **46 commands**.
- Runtime card: `pa lib mod_eq_lcm_iff_pair`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

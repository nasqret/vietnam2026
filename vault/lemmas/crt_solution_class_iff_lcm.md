---
title: "Lemma: crt_solution_class_iff_lcm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_solution_class_iff_lcm`

Relative to one fixed common solution, all solutions are exactly its relational-lcm congruence class.

## Closed Peano statement

```text
forall l m n a b x y. ((((exists hlcm_left_factor_solution_class. l = m * hlcm_left_factor_solution_class) /\ (exists hlcm_right_factor_solution_class. l = n * hlcm_right_factor_solution_class)) /\ forall hlcm_common_solution_class. (exists hlcm_left_common_solution_class. hlcm_common_solution_class = m * hlcm_left_common_solution_class) -> (exists hlcm_right_common_solution_class. hlcm_common_solution_class = n * hlcm_right_common_solution_class) -> exists hlcm_least_factor_solution_class. hlcm_common_solution_class = l * hlcm_least_factor_solution_class)) -> (((exists hgcrt_mod_left_class_fixed_left hgcrt_mod_right_class_fixed_left. x + m * hgcrt_mod_left_class_fixed_left = a + m * hgcrt_mod_right_class_fixed_left) /\ (exists hgcrt_mod_left_class_fixed_right hgcrt_mod_right_class_fixed_right. x + n * hgcrt_mod_left_class_fixed_right = b + n * hgcrt_mod_right_class_fixed_right))) -> (((((exists hgcrt_mod_left_class_candidate_forward_left hgcrt_mod_right_class_candidate_forward_left. y + m * hgcrt_mod_left_class_candidate_forward_left = a + m * hgcrt_mod_right_class_candidate_forward_left) /\ (exists hgcrt_mod_left_class_candidate_forward_right hgcrt_mod_right_class_candidate_forward_right. y + n * hgcrt_mod_left_class_candidate_forward_right = b + n * hgcrt_mod_right_class_candidate_forward_right))) -> (exists hgcrt_mod_left_class_l_forward hgcrt_mod_right_class_l_forward. y + l * hgcrt_mod_left_class_l_forward = x + l * hgcrt_mod_right_class_l_forward)) /\ ((exists hgcrt_mod_left_class_l_reverse hgcrt_mod_right_class_l_reverse. y + l * hgcrt_mod_left_class_l_reverse = x + l * hgcrt_mod_right_class_l_reverse) -> (((exists hgcrt_mod_left_class_candidate_reverse_left hgcrt_mod_right_class_candidate_reverse_left. y + m * hgcrt_mod_left_class_candidate_reverse_left = a + m * hgcrt_mod_right_class_candidate_reverse_left) /\ (exists hgcrt_mod_left_class_candidate_reverse_right hgcrt_mod_right_class_candidate_reverse_right. y + n * hgcrt_mod_left_class_candidate_reverse_right = b + n * hgcrt_mod_right_class_candidate_reverse_right)))))
```

## Dependencies

- [[crt_solution_pair_congruent]]
- [[mod_eq_lcm_iff_pair]]
- [[mod_eq_trans]]

## Checked dependents

- [[crt_solution_unique_lcm_zero]]
- [[crt_solution_canonical_remainder_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2208 nodes**, depth **39**.
- Authored script length: **62 commands**.
- Runtime card: `pa lib crt_solution_class_iff_lcm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

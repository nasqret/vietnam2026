---
title: "Lemma: crt_solution_unique_lcm_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_solution_unique_lcm_zero`

At relational lcm zero, every common solution equals a fixed common solution.

## Closed Peano statement

```text
forall l m n a b x y. l = 0 -> ((((exists hlcm_left_factor_unique_zero. l = m * hlcm_left_factor_unique_zero) /\ (exists hlcm_right_factor_unique_zero. l = n * hlcm_right_factor_unique_zero)) /\ forall hlcm_common_unique_zero. (exists hlcm_left_common_unique_zero. hlcm_common_unique_zero = m * hlcm_left_common_unique_zero) -> (exists hlcm_right_common_unique_zero. hlcm_common_unique_zero = n * hlcm_right_common_unique_zero) -> exists hlcm_least_factor_unique_zero. hlcm_common_unique_zero = l * hlcm_least_factor_unique_zero)) -> (((exists hgcrt_mod_left_unique_zero_fixed_left hgcrt_mod_right_unique_zero_fixed_left. x + m * hgcrt_mod_left_unique_zero_fixed_left = a + m * hgcrt_mod_right_unique_zero_fixed_left) /\ (exists hgcrt_mod_left_unique_zero_fixed_right hgcrt_mod_right_unique_zero_fixed_right. x + n * hgcrt_mod_left_unique_zero_fixed_right = b + n * hgcrt_mod_right_unique_zero_fixed_right))) -> (((exists hgcrt_mod_left_unique_zero_candidate_left hgcrt_mod_right_unique_zero_candidate_left. y + m * hgcrt_mod_left_unique_zero_candidate_left = a + m * hgcrt_mod_right_unique_zero_candidate_left) /\ (exists hgcrt_mod_left_unique_zero_candidate_right hgcrt_mod_right_unique_zero_candidate_right. y + n * hgcrt_mod_left_unique_zero_candidate_right = b + n * hgcrt_mod_right_unique_zero_candidate_right))) -> y = x
```

## Dependencies

- [[crt_solution_class_iff_lcm]]
- [[mod_eq_zero_iff_eq]]

## Checked dependents

- [[generalized_binary_crt_canonical_boundary]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2300 nodes**, depth **40**.
- Authored script length: **33 commands**.
- Runtime card: `pa lib crt_solution_unique_lcm_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

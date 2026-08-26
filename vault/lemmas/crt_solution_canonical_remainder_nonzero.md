---
title: "Lemma: crt_solution_canonical_remainder_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_solution_canonical_remainder_nonzero`

At nonzero relational lcm, every solvable binary CRT system has a unique solution below the lcm.

## Closed Peano statement

```text
forall l m n a b x. ~(l = 0) -> ((((exists hlcm_left_factor_canonical_nonzero. l = m * hlcm_left_factor_canonical_nonzero) /\ (exists hlcm_right_factor_canonical_nonzero. l = n * hlcm_right_factor_canonical_nonzero)) /\ forall hlcm_common_canonical_nonzero. (exists hlcm_left_common_canonical_nonzero. hlcm_common_canonical_nonzero = m * hlcm_left_common_canonical_nonzero) -> (exists hlcm_right_common_canonical_nonzero. hlcm_common_canonical_nonzero = n * hlcm_right_common_canonical_nonzero) -> exists hlcm_least_factor_canonical_nonzero. hlcm_common_canonical_nonzero = l * hlcm_least_factor_canonical_nonzero)) -> (((exists hgcrt_mod_left_canonical_nonzero_fixed_left hgcrt_mod_right_canonical_nonzero_fixed_left. x + m * hgcrt_mod_left_canonical_nonzero_fixed_left = a + m * hgcrt_mod_right_canonical_nonzero_fixed_left) /\ (exists hgcrt_mod_left_canonical_nonzero_fixed_right hgcrt_mod_right_canonical_nonzero_fixed_right. x + n * hgcrt_mod_left_canonical_nonzero_fixed_right = b + n * hgcrt_mod_right_canonical_nonzero_fixed_right))) -> exists r. (((exists hgcrt_below_gap_canonical_nonzero_result. hgcrt_below_gap_canonical_nonzero_result + S r = l) /\ (((exists hgcrt_mod_left_canonical_nonzero_result_left hgcrt_mod_right_canonical_nonzero_result_left. r + m * hgcrt_mod_left_canonical_nonzero_result_left = a + m * hgcrt_mod_right_canonical_nonzero_result_left) /\ (exists hgcrt_mod_left_canonical_nonzero_result_right hgcrt_mod_right_canonical_nonzero_result_right. r + n * hgcrt_mod_left_canonical_nonzero_result_right = b + n * hgcrt_mod_right_canonical_nonzero_result_right)))) /\ ((exists hgcrt_mod_left_canonical_nonzero_result hgcrt_mod_right_canonical_nonzero_result. r + l * hgcrt_mod_left_canonical_nonzero_result = x + l * hgcrt_mod_right_canonical_nonzero_result) /\ forall s. (exists hgcrt_below_gap_canonical_nonzero_comparison. hgcrt_below_gap_canonical_nonzero_comparison + S s = l) -> (((exists hgcrt_mod_left_canonical_nonzero_comparison_left hgcrt_mod_right_canonical_nonzero_comparison_left. s + m * hgcrt_mod_left_canonical_nonzero_comparison_left = a + m * hgcrt_mod_right_canonical_nonzero_comparison_left) /\ (exists hgcrt_mod_left_canonical_nonzero_comparison_right hgcrt_mod_right_canonical_nonzero_comparison_right. s + n * hgcrt_mod_left_canonical_nonzero_comparison_right = b + n * hgcrt_mod_right_canonical_nonzero_comparison_right))) -> s = r))
```

## Dependencies

- [[division_remainder_exists]]
- [[mul_comm]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_symm]]
- [[crt_solution_class_iff_lcm]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[generalized_binary_crt_canonical_boundary]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4086 nodes**, depth **65**.
- Authored script length: **83 commands**.
- Runtime card: `pa lib crt_solution_canonical_remainder_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: generalized_binary_crt_canonical_boundary"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_canonical_boundary`

Every compatible binary CRT system has the correct canonical boundary: exact uniqueness at lcm zero or one unique bounded representative at nonzero lcm.

## Closed Peano statement

```text
forall g l m n a b. ((((exists hag_left_factor_canonical_boundary. m = g * hag_left_factor_canonical_boundary) /\ (exists hag_right_factor_canonical_boundary. n = g * hag_right_factor_canonical_boundary)) /\ forall hag_divisor_canonical_boundary. (exists hag_common_left_canonical_boundary. m = hag_divisor_canonical_boundary * hag_common_left_canonical_boundary) -> (exists hag_common_right_canonical_boundary. n = hag_divisor_canonical_boundary * hag_common_right_canonical_boundary) -> exists hag_greatest_factor_canonical_boundary. g = hag_divisor_canonical_boundary * hag_greatest_factor_canonical_boundary)) -> ((((exists hlcm_left_factor_canonical_boundary. l = m * hlcm_left_factor_canonical_boundary) /\ (exists hlcm_right_factor_canonical_boundary. l = n * hlcm_right_factor_canonical_boundary)) /\ forall hlcm_common_canonical_boundary. (exists hlcm_left_common_canonical_boundary. hlcm_common_canonical_boundary = m * hlcm_left_common_canonical_boundary) -> (exists hlcm_right_common_canonical_boundary. hlcm_common_canonical_boundary = n * hlcm_right_common_canonical_boundary) -> exists hlcm_least_factor_canonical_boundary. hlcm_common_canonical_boundary = l * hlcm_least_factor_canonical_boundary)) -> (exists hgcrt_mod_left_canonical_boundary_compatibility hgcrt_mod_right_canonical_boundary_compatibility. a + g * hgcrt_mod_left_canonical_boundary_compatibility = b + g * hgcrt_mod_right_canonical_boundary_compatibility) -> (((l = 0 /\ exists x. ((((exists hgcrt_mod_left_canonical_boundary_fixed_left hgcrt_mod_right_canonical_boundary_fixed_left. x + m * hgcrt_mod_left_canonical_boundary_fixed_left = a + m * hgcrt_mod_right_canonical_boundary_fixed_left) /\ (exists hgcrt_mod_left_canonical_boundary_fixed_right hgcrt_mod_right_canonical_boundary_fixed_right. x + n * hgcrt_mod_left_canonical_boundary_fixed_right = b + n * hgcrt_mod_right_canonical_boundary_fixed_right))) /\ forall y. (((exists hgcrt_mod_left_canonical_boundary_zero_candidate_left hgcrt_mod_right_canonical_boundary_zero_candidate_left. y + m * hgcrt_mod_left_canonical_boundary_zero_candidate_left = a + m * hgcrt_mod_right_canonical_boundary_zero_candidate_left) /\ (exists hgcrt_mod_left_canonical_boundary_zero_candidate_right hgcrt_mod_right_canonical_boundary_zero_candidate_right. y + n * hgcrt_mod_left_canonical_boundary_zero_candidate_right = b + n * hgcrt_mod_right_canonical_boundary_zero_candidate_right))) -> y = x))) \/ ((~(l = 0) /\ exists r. (((exists hgcrt_below_gap_canonical_boundary_result. hgcrt_below_gap_canonical_boundary_result + S r = l) /\ (((exists hgcrt_mod_left_canonical_boundary_result_left hgcrt_mod_right_canonical_boundary_result_left. r + m * hgcrt_mod_left_canonical_boundary_result_left = a + m * hgcrt_mod_right_canonical_boundary_result_left) /\ (exists hgcrt_mod_left_canonical_boundary_result_right hgcrt_mod_right_canonical_boundary_result_right. r + n * hgcrt_mod_left_canonical_boundary_result_right = b + n * hgcrt_mod_right_canonical_boundary_result_right)))) /\ forall s. (exists hgcrt_below_gap_canonical_boundary_comparison. hgcrt_below_gap_canonical_boundary_comparison + S s = l) -> (((exists hgcrt_mod_left_canonical_boundary_comparison_left hgcrt_mod_right_canonical_boundary_comparison_left. s + m * hgcrt_mod_left_canonical_boundary_comparison_left = a + m * hgcrt_mod_right_canonical_boundary_comparison_left) /\ (exists hgcrt_mod_left_canonical_boundary_comparison_right hgcrt_mod_right_canonical_boundary_comparison_right. s + n * hgcrt_mod_left_canonical_boundary_comparison_right = b + n * hgcrt_mod_right_canonical_boundary_comparison_right))) -> s = r))))
```

## Dependencies

- [[eq_decidable]]
- [[generalized_binary_crt_sufficient]]
- [[crt_solution_unique_lcm_zero]]
- [[crt_solution_canonical_remainder_nonzero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **17750 nodes**, depth **80**.
- Authored script length: **66 commands**.
- Runtime card: `pa lib generalized_binary_crt_canonical_boundary`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

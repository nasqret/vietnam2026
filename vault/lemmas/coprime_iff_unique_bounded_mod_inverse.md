---
title: "Lemma: coprime_iff_unique_bounded_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_iff_unique_bounded_mod_inverse`

For a nonzero modulus, coprimality is equivalent to unique existence of a modular inverse in the canonical interval.

## Closed Peano statement

```text
forall a m. ~(m = 0) -> ((forall hmi_divisor_package_coprime. (exists hmi_left_factor_package_coprime. a = hmi_divisor_package_coprime * hmi_left_factor_package_coprime) -> (exists hmi_right_factor_package_coprime. m = hmi_divisor_package_coprime * hmi_right_factor_package_coprime) -> hmi_divisor_package_coprime = 1) -> (exists hmi_solution_package_result. ((((exists hmi_gap_package_result_chosen_bound. hmi_gap_package_result_chosen_bound + S hmi_solution_package_result = m) /\ (exists hmi_left_offset_package_result_chosen_inverse hmi_right_offset_package_result_chosen_inverse. a * hmi_solution_package_result + m * hmi_left_offset_package_result_chosen_inverse = 1 + m * hmi_right_offset_package_result_chosen_inverse))) /\ forall hmi_comparison_package_result. (((exists hmi_gap_package_result_compared_bound. hmi_gap_package_result_compared_bound + S hmi_comparison_package_result = m) /\ (exists hmi_left_offset_package_result_compared_inverse hmi_right_offset_package_result_compared_inverse. a * hmi_comparison_package_result + m * hmi_left_offset_package_result_compared_inverse = 1 + m * hmi_right_offset_package_result_compared_inverse))) -> hmi_comparison_package_result = hmi_solution_package_result))) /\ ((exists hmi_solution_package_result. ((((exists hmi_gap_package_result_chosen_bound. hmi_gap_package_result_chosen_bound + S hmi_solution_package_result = m) /\ (exists hmi_left_offset_package_result_chosen_inverse hmi_right_offset_package_result_chosen_inverse. a * hmi_solution_package_result + m * hmi_left_offset_package_result_chosen_inverse = 1 + m * hmi_right_offset_package_result_chosen_inverse))) /\ forall hmi_comparison_package_result. (((exists hmi_gap_package_result_compared_bound. hmi_gap_package_result_compared_bound + S hmi_comparison_package_result = m) /\ (exists hmi_left_offset_package_result_compared_inverse hmi_right_offset_package_result_compared_inverse. a * hmi_comparison_package_result + m * hmi_left_offset_package_result_compared_inverse = 1 + m * hmi_right_offset_package_result_compared_inverse))) -> hmi_comparison_package_result = hmi_solution_package_result)) -> (forall hmi_divisor_package_coprime. (exists hmi_left_factor_package_coprime. a = hmi_divisor_package_coprime * hmi_left_factor_package_coprime) -> (exists hmi_right_factor_package_coprime. m = hmi_divisor_package_coprime * hmi_right_factor_package_coprime) -> hmi_divisor_package_coprime = 1))
```

## Dependencies

- [[coprime_bounded_mod_inverse]]
- [[bounded_mod_inverse_unique]]
- [[mod_inverse_implies_coprime]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **9512 nodes**, depth **70**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib coprime_iff_unique_bounded_mod_inverse`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: generalized_binary_crt_solvable_iff"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_solvable_iff`

For arbitrary natural moduli, a binary CRT system is solvable exactly when its residues are congruent modulo a relational gcd.

## Closed Peano statement

```text
forall g m n a b. ((((exists hag_left_factor_total_iff_gcd. m = g * hag_left_factor_total_iff_gcd) /\ (exists hag_right_factor_total_iff_gcd. n = g * hag_right_factor_total_iff_gcd)) /\ forall hag_divisor_total_iff_gcd. (exists hag_common_left_total_iff_gcd. m = hag_divisor_total_iff_gcd * hag_common_left_total_iff_gcd) -> (exists hag_common_right_total_iff_gcd. n = hag_divisor_total_iff_gcd * hag_common_right_total_iff_gcd) -> exists hag_greatest_factor_total_iff_gcd. g = hag_divisor_total_iff_gcd * hag_greatest_factor_total_iff_gcd)) -> (((exists x. (((exists hgcrt_mod_left_total_iff_forward_solution_left hgcrt_mod_right_total_iff_forward_solution_left. x + m * hgcrt_mod_left_total_iff_forward_solution_left = a + m * hgcrt_mod_right_total_iff_forward_solution_left) /\ (exists hgcrt_mod_left_total_iff_forward_solution_right hgcrt_mod_right_total_iff_forward_solution_right. x + n * hgcrt_mod_left_total_iff_forward_solution_right = b + n * hgcrt_mod_right_total_iff_forward_solution_right)))) -> (exists hgcrt_mod_left_total_iff_forward_compatibility hgcrt_mod_right_total_iff_forward_compatibility. a + g * hgcrt_mod_left_total_iff_forward_compatibility = b + g * hgcrt_mod_right_total_iff_forward_compatibility)) /\ ((exists hgcrt_mod_left_total_iff_reverse_compatibility hgcrt_mod_right_total_iff_reverse_compatibility. a + g * hgcrt_mod_left_total_iff_reverse_compatibility = b + g * hgcrt_mod_right_total_iff_reverse_compatibility) -> exists x. (((exists hgcrt_mod_left_total_iff_reverse_solution_left hgcrt_mod_right_total_iff_reverse_solution_left. x + m * hgcrt_mod_left_total_iff_reverse_solution_left = a + m * hgcrt_mod_right_total_iff_reverse_solution_left) /\ (exists hgcrt_mod_left_total_iff_reverse_solution_right hgcrt_mod_right_total_iff_reverse_solution_right. x + n * hgcrt_mod_left_total_iff_reverse_solution_right = b + n * hgcrt_mod_right_total_iff_reverse_solution_right)))))
```

## Dependencies

- [[crt_common_solution_implies_gcd_compatible]]
- [[generalized_binary_crt_sufficient]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **11825 nodes**, depth **80**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib generalized_binary_crt_solvable_iff`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: crt_common_solution_implies_gcd_compatible"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_common_solution_implies_gcd_compatible`

A common CRT solution forces the residues to be congruent modulo every relational gcd.

## Closed Peano statement

```text
forall g m n a b x. ((((exists hag_left_factor_crt_necessity. m = g * hag_left_factor_crt_necessity) /\ (exists hag_right_factor_crt_necessity. n = g * hag_right_factor_crt_necessity)) /\ forall hag_divisor_crt_necessity. (exists hag_common_left_crt_necessity. m = hag_divisor_crt_necessity * hag_common_left_crt_necessity) -> (exists hag_common_right_crt_necessity. n = hag_divisor_crt_necessity * hag_common_right_crt_necessity) -> exists hag_greatest_factor_crt_necessity. g = hag_divisor_crt_necessity * hag_greatest_factor_crt_necessity)) -> (((exists hgcrt_mod_left_necessity_solution_left hgcrt_mod_right_necessity_solution_left. x + m * hgcrt_mod_left_necessity_solution_left = a + m * hgcrt_mod_right_necessity_solution_left) /\ (exists hgcrt_mod_left_necessity_solution_right hgcrt_mod_right_necessity_solution_right. x + n * hgcrt_mod_left_necessity_solution_right = b + n * hgcrt_mod_right_necessity_solution_right))) -> (exists hgcrt_mod_left_necessity_compatibility hgcrt_mod_right_necessity_compatibility. a + g * hgcrt_mod_left_necessity_compatibility = b + g * hgcrt_mod_right_necessity_compatibility)
```

## Dependencies

- [[is_gcd_dvd_left]]
- [[is_gcd_dvd_right]]
- [[mod_eq_of_mod_eq_multiple]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]

## Checked dependents

- [[crt_incompatibility_obstructs_solution]]
- [[generalized_binary_crt_solvable_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **518 nodes**, depth **34**.
- Authored script length: **50 commands**.
- Runtime card: `pa lib crt_common_solution_implies_gcd_compatible`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

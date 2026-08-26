---
title: "Lemma: generalized_binary_crt_solution_or_obstruction"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_solution_or_obstruction`

Every generalized binary CRT instance constructively returns a solution or a certified incompatibility obstruction.

## Closed Peano statement

```text
forall g m n a b. ((((exists hag_left_factor_decision_boundary. m = g * hag_left_factor_decision_boundary) /\ (exists hag_right_factor_decision_boundary. n = g * hag_right_factor_decision_boundary)) /\ forall hag_divisor_decision_boundary. (exists hag_common_left_decision_boundary. m = hag_divisor_decision_boundary * hag_common_left_decision_boundary) -> (exists hag_common_right_decision_boundary. n = hag_divisor_decision_boundary * hag_common_right_decision_boundary) -> exists hag_greatest_factor_decision_boundary. g = hag_divisor_decision_boundary * hag_greatest_factor_decision_boundary)) -> (((exists hgcrt_mod_left_decision_boundary_compatible hgcrt_mod_right_decision_boundary_compatible. a + g * hgcrt_mod_left_decision_boundary_compatible = b + g * hgcrt_mod_right_decision_boundary_compatible) /\ exists x. (((exists hgcrt_mod_left_decision_boundary_positive_left hgcrt_mod_right_decision_boundary_positive_left. x + m * hgcrt_mod_left_decision_boundary_positive_left = a + m * hgcrt_mod_right_decision_boundary_positive_left) /\ (exists hgcrt_mod_left_decision_boundary_positive_right hgcrt_mod_right_decision_boundary_positive_right. x + n * hgcrt_mod_left_decision_boundary_positive_right = b + n * hgcrt_mod_right_decision_boundary_positive_right)))) \/ (~(exists hgcrt_mod_left_decision_boundary_incompatible hgcrt_mod_right_decision_boundary_incompatible. a + g * hgcrt_mod_left_decision_boundary_incompatible = b + g * hgcrt_mod_right_decision_boundary_incompatible) /\ ~(exists x. (((exists hgcrt_mod_left_decision_boundary_negative_left hgcrt_mod_right_decision_boundary_negative_left. x + m * hgcrt_mod_left_decision_boundary_negative_left = a + m * hgcrt_mod_right_decision_boundary_negative_left) /\ (exists hgcrt_mod_left_decision_boundary_negative_right hgcrt_mod_right_decision_boundary_negative_right. x + n * hgcrt_mod_left_decision_boundary_negative_right = b + n * hgcrt_mod_right_decision_boundary_negative_right))))))
```

## Dependencies

- [[mod_eq_decidable]]
- [[generalized_binary_crt_sufficient]]
- [[crt_incompatibility_obstructs_solution]]

## Checked dependents

- [[generalized_binary_crt_total_decision]]

## Verification record

- Independently checked from the empty context.
- Certificate: **14182 nodes**, depth **80**.
- Authored script length: **36 commands**.
- Runtime card: `pa lib generalized_binary_crt_solution_or_obstruction`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: generalized_binary_crt_total_decision"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `generalized_binary_crt_total_decision`

Every raw binary CRT input returns a relational gcd and either a solution or a certified incompatibility obstruction.

## Closed Peano statement

```text
forall m n a b. exists g. (((((exists hag_left_factor_total_decision. m = g * hag_left_factor_total_decision) /\ (exists hag_right_factor_total_decision. n = g * hag_right_factor_total_decision)) /\ forall hag_divisor_total_decision. (exists hag_common_left_total_decision. m = hag_divisor_total_decision * hag_common_left_total_decision) -> (exists hag_common_right_total_decision. n = hag_divisor_total_decision * hag_common_right_total_decision) -> exists hag_greatest_factor_total_decision. g = hag_divisor_total_decision * hag_greatest_factor_total_decision)) /\ (((exists hgcrt_mod_left_total_decision_compatible hgcrt_mod_right_total_decision_compatible. a + g * hgcrt_mod_left_total_decision_compatible = b + g * hgcrt_mod_right_total_decision_compatible) /\ exists x. (((exists hgcrt_mod_left_total_decision_positive_left hgcrt_mod_right_total_decision_positive_left. x + m * hgcrt_mod_left_total_decision_positive_left = a + m * hgcrt_mod_right_total_decision_positive_left) /\ (exists hgcrt_mod_left_total_decision_positive_right hgcrt_mod_right_total_decision_positive_right. x + n * hgcrt_mod_left_total_decision_positive_right = b + n * hgcrt_mod_right_total_decision_positive_right)))) \/ (~(exists hgcrt_mod_left_total_decision_incompatible hgcrt_mod_right_total_decision_incompatible. a + g * hgcrt_mod_left_total_decision_incompatible = b + g * hgcrt_mod_right_total_decision_incompatible) /\ ~(exists x. (((exists hgcrt_mod_left_total_decision_negative_left hgcrt_mod_right_total_decision_negative_left. x + m * hgcrt_mod_left_total_decision_negative_left = a + m * hgcrt_mod_right_total_decision_negative_left) /\ (exists hgcrt_mod_left_total_decision_negative_right hgcrt_mod_right_total_decision_negative_right. x + n * hgcrt_mod_left_total_decision_negative_right = b + n * hgcrt_mod_right_total_decision_negative_right)))))))
```

## Dependencies

- [[gcd_exists_relational]]
- [[generalized_binary_crt_solution_or_obstruction]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **15492 nodes**, depth **82**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib generalized_binary_crt_total_decision`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: crt_scaled_common_remainder_lift"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_scaled_common_remainder_lift`

A coprime cofactor CRT solution scales and lifts through a common remainder.

## Closed Peano statement

```text
forall g m n a b M N A B r. m = g * M -> n = g * N -> a = g * A + r -> b = g * B + r -> ~(M = 0) -> ~(N = 0) -> (forall hmi_divisor_lift_assumption. (exists hmi_left_factor_lift_assumption. M = hmi_divisor_lift_assumption * hmi_left_factor_lift_assumption) -> (exists hmi_right_factor_lift_assumption. N = hmi_divisor_lift_assumption * hmi_right_factor_lift_assumption) -> hmi_divisor_lift_assumption = 1) -> exists x. (((exists hgcrt_mod_left_lift_result_left hgcrt_mod_right_lift_result_left. x + m * hgcrt_mod_left_lift_result_left = a + m * hgcrt_mod_right_lift_result_left) /\ (exists hgcrt_mod_left_lift_result_right hgcrt_mod_right_lift_result_right. x + n * hgcrt_mod_left_lift_result_right = b + n * hgcrt_mod_right_lift_result_right)))
```

## Dependencies

- [[binary_crt]]
- [[mod_eq_scale]]
- [[mod_eq_refl]]
- [[mod_eq_add]]

## Checked dependents

- [[generalized_binary_crt_sufficient_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5745 nodes**, depth **52**.
- Authored script length: **78 commands**.
- Runtime card: `pa lib crt_scaled_common_remainder_lift`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: is_lcm_scale_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_scale_nonzero`

A nonzero common left scale preserves the universal relational LCM specification.

## Closed Peano statement

```text
forall k l a b. ~(k = 0) -> ((((exists hscale_left_factor_source. l = a * hscale_left_factor_source) /\ (exists hscale_right_factor_source. l = b * hscale_right_factor_source)) /\ forall hscale_common_source. (exists hscale_left_common_source. hscale_common_source = a * hscale_left_common_source) -> (exists hscale_right_common_source. hscale_common_source = b * hscale_right_common_source) -> exists hscale_least_factor_source. hscale_common_source = l * hscale_least_factor_source)) -> ((((exists hscale_left_factor_target. (k * l) = (k * a) * hscale_left_factor_target) /\ (exists hscale_right_factor_target. (k * l) = (k * b) * hscale_right_factor_target)) /\ forall hscale_common_target. (exists hscale_left_common_target. hscale_common_target = (k * a) * hscale_left_common_target) -> (exists hscale_right_common_target. hscale_common_target = (k * b) * hscale_right_common_target) -> exists hscale_least_factor_target. hscale_common_target = (k * l) * hscale_least_factor_target))
```

## Dependencies

- [[mul_assoc]]
- [[mul_left_cancel_nonzero]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **430 nodes**, depth **27**.
- Authored script length: **60 commands**.
- Runtime card: `pa lib is_lcm_scale_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

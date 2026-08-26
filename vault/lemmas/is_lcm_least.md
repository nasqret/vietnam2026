---
title: "Lemma: is_lcm_least"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_lcm_least`

A relational lcm divides every common multiple.

## Closed Peano statement

```text
forall l a b c. ((((exists hlcm_left_factor_least. l = a * hlcm_left_factor_least) /\ (exists hlcm_right_factor_least. l = b * hlcm_right_factor_least)) /\ forall hlcm_common_least. (exists hlcm_left_common_least. hlcm_common_least = a * hlcm_left_common_least) -> (exists hlcm_right_common_least. hlcm_common_least = b * hlcm_right_common_least) -> exists hlcm_least_factor_least. hlcm_common_least = l * hlcm_least_factor_least)) -> (exists x. c = a * x) -> (exists y. c = b * y) -> exists z. c = l * z
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mod_eq_lcm_merge]]

## Verification record

- Independently checked from the empty context.
- Certificate: **24 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib is_lcm_least`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

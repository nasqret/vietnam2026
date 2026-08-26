---
title: "Lemma: is_gcd_zero_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_zero_right`

Every natural is the relational gcd of itself and zero.

## Closed Peano statement

```text
forall a. (((exists x. a = a * x) /\ (exists y. 0 = a * y)) /\ forall c. (exists u. a = c * u) -> (exists v. 0 = c * v) -> exists w. a = c * w)
```

## Dependencies

- [[multiple_refl]]
- [[multiple_zero]]

## Checked dependents

- [[gcd_balanced_bezout_exists_up_to]]
- [[generalized_binary_crt_sufficient_zero_left]]
- [[generalized_binary_crt_sufficient_zero_right]]

## Verification record

- Independently checked from the empty context.
- Certificate: **65 nodes**, depth **11**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib is_gcd_zero_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

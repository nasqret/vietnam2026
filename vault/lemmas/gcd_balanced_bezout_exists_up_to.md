---
title: "Lemma: gcd_balanced_bezout_exists_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_balanced_bezout_exists_up_to`

Bounded Euclidean descent simultaneously constructs a relational gcd and balanced natural Bezout witnesses.

## Closed Peano statement

```text
forall B b. (exists t. t + b = B) -> forall a. exists d. ((((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w) /\ exists xp yp xn yn. a * xp + b * yp = d + (a * xn + b * yn))
```

## Dependencies

- [[zero_add]]
- [[le_zero]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]
- [[division_remainder_exists]]
- [[is_gcd_zero_right]]
- [[is_gcd_euclid_forward]]
- [[balanced_bezout_euclid_step]]

## Checked dependents

- [[gcd_balanced_bezout_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2233 nodes**, depth **45**.
- Authored script length: **80 commands**.
- Runtime card: `pa lib gcd_balanced_bezout_exists_up_to`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

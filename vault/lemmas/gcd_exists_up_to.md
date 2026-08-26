---
title: "Lemma: gcd_exists_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_exists_up_to`

Bounded induction constructs a relational gcd whenever the right input is at most the bound.

## Closed Peano statement

```text
forall B b. (exists t. t + b = B) -> forall a. exists d. (((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w)
```

## Dependencies

- [[multiple_refl]]
- [[le_zero]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]
- [[division_remainder_exists]]
- [[is_gcd_euclid_forward]]

## Checked dependents

- [[gcd_exists_relational]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1232 nodes**, depth **44**.
- Authored script length: **74 commands**.
- Runtime card: `pa lib gcd_exists_up_to`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

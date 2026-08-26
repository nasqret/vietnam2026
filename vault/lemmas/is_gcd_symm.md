---
title: "Lemma: is_gcd_symm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_symm`

The expanded relational greatest-common-divisor specification is symmetric.

## Closed Peano statement

```text
forall g a b. (((exists x. a = g * x) /\ (exists y. b = g * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. g = c * w) -> ((exists x. b = g * x) /\ (exists y. a = g * y)) /\ forall c. (exists u. b = c * u) -> (exists v. a = c * v) -> exists w. g = c * w
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[generalized_binary_crt_sufficient_zero_left]]

## Verification record

- Independently checked from the empty context.
- Certificate: **36 nodes**, depth **21**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib is_gcd_symm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: is_gcd_dvd_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_dvd_left`

A relational greatest common divisor divides its left input.

## Closed Peano statement

```text
forall g a b. (((exists x. a = g * x) /\ (exists y. b = g * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. g = c * w) -> exists x. a = g * x
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[crt_common_solution_implies_gcd_compatible]]
- [[generalized_binary_crt_sufficient_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **13**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib is_gcd_dvd_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: divides_linear_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `divides_linear_step`

A common divisor of a divisor and remainder divides their Euclidean linear step.

## Closed Peano statement

```text
forall c b q r. (exists u. b = c * u) -> (exists v. r = c * v) -> exists w. b * q + r = c * w
```

## Dependencies

- [[mul_assoc]]
- [[mul_add]]

## Checked dependents

- [[is_gcd_euclid_forward]]
- [[is_gcd_euclid_backward]]

## Verification record

- Independently checked from the empty context.
- Certificate: **194 nodes**, depth **43**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib divides_linear_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

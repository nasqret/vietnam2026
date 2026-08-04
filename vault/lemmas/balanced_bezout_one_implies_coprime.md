---
title: "Lemma: balanced_bezout_one_implies_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `balanced_bezout_one_implies_coprime`

A balanced natural Bezout equation with result one forces the two inputs to be coprime.

## Closed Peano statement

```text
forall a b xp yp xn yn. a * xp + b * yp = 1 + (a * xn + b * yn) -> forall d. (exists u. a = d * u) -> (exists v. b = d * v) -> d = 1
```

## Dependencies

- [[common_divisor_divides_balanced_result]]
- [[divisor_one]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **871 nodes**, depth **40**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib balanced_bezout_one_implies_coprime`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

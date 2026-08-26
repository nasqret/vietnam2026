---
title: "Lemma: common_divisor_divides_balanced_result"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `common_divisor_divides_balanced_result`

Every common divisor of two inputs divides the result of a balanced natural combination.

## Closed Peano statement

```text
forall c a b d xp yp xn yn. (exists u. a = c * u) -> (exists v. b = c * v) -> a * xp + b * yp = d + (a * xn + b * yn) -> exists w. d = c * w
```

## Dependencies

- [[mul_assoc]]
- [[mul_add]]
- [[add_comm]]
- [[factor_difference]]

## Checked dependents

- [[gauss_coprime_cancel]]
- [[mod_inverse_implies_coprime]]
- [[balanced_bezout_one_implies_coprime]]

## Verification record

- Independently checked from the empty context.
- Certificate: **626 nodes**, depth **39**.
- Authored script length: **48 commands**.
- Runtime card: `pa lib common_divisor_divides_balanced_result`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: divides_remainder"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `divides_remainder`

A common divisor of a dividend and divisor also divides the remainder.

## Closed Peano statement

```text
forall c a b q r. (exists u. a = c * u) -> (exists v. b = c * v) -> a = b * q + r -> exists w. r = c * w
```

## Dependencies

- [[mul_assoc]]
- [[factor_difference]]

## Checked dependents

- [[is_gcd_euclid_forward]]
- [[is_gcd_euclid_backward]]
- [[beta_modulus_coprime_base]]
- [[common_divisor_beta_moduli_divides_gap_times_c]]

## Verification record

- Independently checked from the empty context.
- Certificate: **427 nodes**, depth **29**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib divides_remainder`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

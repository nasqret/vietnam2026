---
title: "Lemma: balanced_bezout_euclid_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `balanced_bezout_euclid_step`

Transport balanced natural Bezout coefficients across one Euclidean division step.

## Closed Peano statement

```text
forall a b q r d xp yp xn yn. a = b * q + r -> b * xp + r * yp = d + (b * xn + r * yn) -> a * yp + b * (xp + q * yn) = d + (a * yn + b * (xn + q * yp))
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]
- [[mul_add]]
- [[mul_assoc]]
- [[add_mul]]
- [[add_permute_outer]]

## Checked dependents

- [[gcd_balanced_bezout_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **880 nodes**, depth **35**.
- Authored script length: **67 commands**.
- Runtime card: `pa lib balanced_bezout_euclid_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

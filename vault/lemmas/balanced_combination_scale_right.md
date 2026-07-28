---
title: "Lemma: balanced_combination_scale_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `balanced_combination_scale_right`

Scale a balanced natural combination on the right.

## Closed Peano statement

```text
forall a b d xp yp xn yn z. a * xp + b * yp = d + (a * xn + b * yn) -> a * (xp * z) + (b * z) * yp = d * z + (a * (xn * z) + (b * z) * yn)
```

## Dependencies

- [[mul_assoc]]
- [[mul_comm]]
- [[add_mul]]

## Checked dependents

- [[gauss_coprime_cancel]]

## Verification record

- Independently checked from the empty context.
- Certificate: **754 nodes**, depth **28**.
- Authored script length: **56 commands**.
- Runtime card: `pa lib balanced_combination_scale_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: balanced_bezout_cancel_gcd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `balanced_bezout_cancel_gcd`

Cancel a nonzero common gcd factor from a balanced Bezout equation.

## Closed Peano statement

```text
forall g a b A B xp yp xn yn. ~(g = 0) -> a = g * A -> b = g * B -> a * xp + b * yp = g + (a * xn + b * yn) -> A * xp + B * yp = 1 + (A * xn + B * yn)
```

## Dependencies

- [[mul_left_cancel_nonzero]]
- [[mul_add]]
- [[mul_assoc]]
- [[mul_one]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **549 nodes**, depth **38**.
- Authored script length: **54 commands**.
- Runtime card: `pa lib balanced_bezout_cancel_gcd`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

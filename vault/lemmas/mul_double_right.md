---
title: "Lemma: mul_double_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_double_right`

Doubling commutes through multiplication on the right.

## Closed Peano statement

```text
forall m b. m * (2 * b) = 2 * (m * b)
```

## Dependencies

- [[mul_assoc]]
- [[mul_comm]]

## Checked dependents

- [[even_mul_right]]
- [[odd_mul_odd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **356 nodes**, depth **26**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib mul_double_right`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

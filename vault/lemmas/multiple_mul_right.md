---
title: "Lemma: multiple_mul_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_mul_right`

A right multiple of a multiple remains a multiple.

## Closed Peano statement

```text
forall a n m. (exists q. n = a * q) -> exists s. n * m = a * s
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- [[multiple_mul_left]]

## Verification record

- Independently checked from the empty context.
- Certificate: **113 nodes**, depth **37**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib multiple_mul_right`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: even_mul_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_mul_left`

A product with an even left factor is even.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a) -> exists c. m * n = 2 * c
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **130 nodes**, depth **18**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib even_mul_left`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

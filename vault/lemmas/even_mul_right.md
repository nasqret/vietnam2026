---
title: "Lemma: even_mul_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_mul_right`

A product with an even right factor is even.

## Closed Peano statement

```text
forall m n. (exists b. n = 2 * b) -> exists c. m * n = 2 * c
```

## Dependencies

- [[mul_double_right]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **369 nodes**, depth **27**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib even_mul_right`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

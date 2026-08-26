---
title: "Lemma: even_add_even"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_add_even`

The sum of two even naturals is even.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a) -> (exists b. n = 2 * b) -> exists c. m + n = 2 * c
```

## Dependencies

- [[mul_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **100 nodes**, depth **17**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib even_add_even`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

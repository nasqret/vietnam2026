---
title: "Lemma: multiple_add"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_add`

Multiples of a fixed number are closed under addition.

## Closed Peano statement

```text
forall a n m. (exists q. n = a * q) -> (exists r. m = a * r) -> exists s. n + m = a * s
```

## Dependencies

- [[mul_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **87 nodes**, depth **32**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib multiple_add`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

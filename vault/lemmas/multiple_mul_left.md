---
title: "Lemma: multiple_mul_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_mul_left`

A left multiple of a multiple remains a multiple.

## Closed Peano statement

```text
forall a n m. (exists q. n = a * q) -> exists s. m * n = a * s
```

## Dependencies

- [[mul_comm]]
- [[multiple_mul_right]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **370 nodes**, depth **25**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib multiple_mul_left`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

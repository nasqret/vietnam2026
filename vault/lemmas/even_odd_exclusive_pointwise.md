---
title: "Lemma: even_odd_exclusive_pointwise"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_odd_exclusive_pointwise`

An even and an odd decomposition of the same natural are incompatible.

## Closed Peano statement

```text
forall n a b. n = 2 * a -> n = 2 * b + 1 -> false
```

## Dependencies

- [[division_remainder_unique]]

## Checked dependents

- [[even_not_odd]]
- [[odd_not_even]]

## Verification record

- Independently checked from the empty context.
- Certificate: **928 nodes**, depth **58**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib even_odd_exclusive_pointwise`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

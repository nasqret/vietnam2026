---
title: "Lemma: even_not_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_not_odd`

No even natural is odd.

## Closed Peano statement

```text
forall n. (exists a. n = 2 * a) -> ~(exists b. n = 2 * b + 1)
```

## Dependencies

- [[even_odd_exclusive_pointwise]]

## Checked dependents

- [[even_successor_to_odd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **953 nodes**, depth **59**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib even_not_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

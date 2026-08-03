---
title: "Lemma: even_successor_to_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_successor_to_odd`

If a successor is even, its predecessor is odd.

## Closed Peano statement

```text
forall n. (exists a. S n = 2 * a) -> exists b. n = 2 * b + 1
```

## Dependencies

- [[parity_cases]]
- [[successor_odd_of_even]]
- [[even_not_odd]]

## Checked dependents

- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1074 nodes**, depth **62**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib even_successor_to_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

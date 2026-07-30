---
title: "Lemma: odd_not_even"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_not_even`

No odd natural is even.

## Closed Peano statement

```text
forall n. (exists b. n = 2 * b + 1) -> ~(exists a. n = 2 * a)
```

## Dependencies

- [[even_odd_exclusive_pointwise]]

## Checked dependents

- [[odd_successor_to_even]]
- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **953 nodes**, depth **59**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib odd_not_even`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

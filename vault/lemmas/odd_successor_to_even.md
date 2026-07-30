---
title: "Lemma: odd_successor_to_even"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_successor_to_even`

If a successor is odd, its predecessor is even.

## Closed Peano statement

```text
forall n. (exists a. S n = 2 * a + 1) -> exists b. n = 2 * b
```

## Dependencies

- [[parity_cases]]
- [[successor_even_of_odd]]
- [[odd_not_even]]

## Checked dependents

- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1102 nodes**, depth **62**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib odd_successor_to_even`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

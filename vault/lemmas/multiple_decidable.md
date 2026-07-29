---
title: "Lemma: multiple_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_decidable`

Divisibility of natural numbers is constructively decidable, including the zero divisor case.

## Closed Peano statement

```text
forall d n. (exists q. n = d * q) \/ ~(exists q. n = d * q)
```

## Dependencies

- [[mul_zero_left]]
- [[eq_decidable]]
- [[multiple_decidable_nonzero]]

## Checked dependents

- [[prime_divides_decidable]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1352 nodes**, depth **64**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib multiple_decidable`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

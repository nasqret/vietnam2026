---
title: "Lemma: multiple_has_zero_remainder"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_has_zero_remainder`

Every multiple of a nonzero divisor has a bounded zero-remainder decomposition.

## Closed Peano statement

```text
forall m n. ~(m = 0) -> (exists q. n = m * q) -> exists q r. (n = m * q + r /\ r = 0) /\ S r <= m
```

## Dependencies

- [[zero_or_succ]]

## Checked dependents

- [[multiple_decidable_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **54 nodes**, depth **20**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib multiple_has_zero_remainder`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

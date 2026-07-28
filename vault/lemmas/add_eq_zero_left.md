---
title: "Lemma: add_eq_zero_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_eq_zero_left`

A sum equal to zero has zero as its left addend.

## Closed Peano statement

```text
forall a b. a + b = 0 -> a = 0
```

## Dependencies

- [[add_comm]]
- [[add_eq_zero_right]]

## Checked dependents

- [[add_eq_zero_components]]
- [[two_large_factors_impossible]]
- [[bounded_common_multiple_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **112 nodes**, depth **14**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib add_eq_zero_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

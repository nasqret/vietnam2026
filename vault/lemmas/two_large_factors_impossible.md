---
title: "Lemma: two_large_factors_impossible"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `two_large_factors_impossible`

Two naturals at least two cannot multiply to two.

## Closed Peano statement

```text
forall a b. ~(2 = S (S a) * S (S b))
```

## Dependencies

- [[mul_succ_left]]
- [[add_eq_zero_left]]
- [[mul_eq_zero]]

## Checked dependents

- [[prime_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **376 nodes**, depth **23**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib two_large_factors_impossible`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

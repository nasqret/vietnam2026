---
title: "Lemma: proper_factor_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `proper_factor_lt`

A factor with a nonunit cofactor is strictly smaller than a nonzero product.

## Closed Peano statement

```text
forall n c d. ~(n = 0) -> n = c * d -> ~(d = 1) -> exists k. k + S c = n
```

## Dependencies

- [[divisor_le_nonzero]]
- [[le_eq_or_lt]]
- [[mul_left_cancel_nonzero]]
- [[mul_one]]

## Checked dependents

- [[prime_divisor_exists_up_to]]
- [[greatest_prime_divisor_descent]]

## Verification record

- Independently checked from the empty context.
- Certificate: **468 nodes**, depth **26**.
- Authored script length: **43 commands**.
- Runtime card: `pa lib proper_factor_lt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

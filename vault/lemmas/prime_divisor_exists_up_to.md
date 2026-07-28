---
title: "Lemma: prime_divisor_exists_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_divisor_exists_up_to`

Bounded strong induction constructs a prime divisor of every nonzero nonunit natural.

## Closed Peano statement

```text
forall B n. (exists t. t + n = B) -> ~(n = 0) -> ~(n = 1) -> exists p. ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\ exists k. n = p * k)
```

## Dependencies

- [[mul_zero_left]]
- [[le_zero]]
- [[lt_of_lt_of_le]]
- [[le_of_succ_le_succ]]
- [[multiple_refl]]
- [[multiple_trans]]
- [[prime_or_composite]]
- [[proper_factor_lt]]

## Checked dependents

- [[prime_divisor_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2931 nodes**, depth **78**.
- Authored script length: **71 commands**.
- Runtime card: `pa lib prime_divisor_exists_up_to`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

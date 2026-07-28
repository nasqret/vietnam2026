---
title: "Lemma: bounded_common_multiple_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_common_multiple_step`

Extend a nonzero common multiple through the next positive natural.

## Closed Peano statement

```text
forall B c. ~(c = 0) -> (forall t. (exists h. S t + S h = S B) -> exists k. c = S t * k) -> exists c2. (~(c2 = 0) /\ forall t. (exists h. S t + S h = S (S B)) -> exists k. c2 = S t * k)
```

## Dependencies

- [[mul_eq_zero]]
- [[succ_ne_zero]]
- [[zero_or_succ]]
- [[multiple_mul_right]]
- [[mul_comm]]

## Checked dependents

- [[bounded_common_multiple_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **483 nodes**, depth **29**.
- Authored script length: **52 commands**.
- Runtime card: `pa lib bounded_common_multiple_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

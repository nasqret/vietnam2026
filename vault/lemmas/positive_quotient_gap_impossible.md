---
title: "Lemma: positive_quotient_gap_impossible"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `positive_quotient_gap_impossible`

A positive gap between quotients makes two bounded-remainder decompositions unequal.

## Closed Peano statement

```text
forall m q q2 r s k. (exists z. z + S r = m) -> S k + q = q2 -> ~(m * q + r = m * q2 + s)
```

## Dependencies

- [[add_comm]]
- [[add_assoc]]
- [[mul_add]]
- [[add_left_cancel]]
- [[lt_not_eq_add_middle]]

## Checked dependents

- [[division_remainder_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **464 nodes**, depth **41**.
- Authored script length: **34 commands**.
- Runtime card: `pa lib positive_quotient_gap_impossible`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

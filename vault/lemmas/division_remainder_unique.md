---
title: "Lemma: division_remainder_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `division_remainder_unique`

Bounded quotient-remainder decompositions have unique quotients and remainders.

## Closed Peano statement

```text
forall m n q r q2 r2. n = m * q + r -> (exists k. k + S r = m) -> n = m * q2 + r2 -> (exists k. k + S r2 = m) -> q = q2 /\ r = r2
```

## Dependencies

- [[zero_add]]
- [[le_total]]
- [[zero_or_succ]]
- [[add_left_cancel]]
- [[positive_quotient_gap_impossible]]

## Checked dependents

- [[multiple_decidable_nonzero]]
- [[beta_at_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **854 nodes**, depth **57**.
- Authored script length: **74 commands**.
- Runtime card: `pa lib division_remainder_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

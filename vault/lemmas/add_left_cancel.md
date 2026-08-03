---
title: "Lemma: add_left_cancel"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_left_cancel`

A common left addend can be cancelled.

## Closed Peano statement

```text
forall a b c. a + b = a + c -> b = c
```

## Dependencies

- [[add_comm]]
- [[add_right_cancel]]

## Checked dependents

- [[positive_quotient_gap_impossible]]
- [[remainder_unique_same_quotient]]
- [[division_remainder_unique]]
- [[beta_range_injective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **143 nodes**, depth **18**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib add_left_cancel`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

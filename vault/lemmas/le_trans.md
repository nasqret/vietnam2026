---
title: "Lemma: le_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_trans`

Order witnesses compose by addition, so the defined order is transitive.

## Closed Peano statement

```text
forall n m k. n <= m -> m <= k -> n <= k
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- [[lt_of_lt_of_le]]

## Verification record

- Independently checked from the empty context.
- Certificate: **51 nodes**, depth **21**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

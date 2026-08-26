---
title: "Lemma: factor_search_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factor_search_up_to`

Constructively decide whether a nonzero natural has a bounded nontrivial factor pair.

## Closed Peano statement

```text
forall B n. ~(n = 0) -> ((forall c d. (exists k. k + c = B) -> n = c * d -> c = 1 \/ d = 1) \/ exists c d. ((((exists k. k + c = B) /\ ~(c = 1)) /\ ~(d = 1)) /\ n = c * d))
```

## Dependencies

- [[mul_zero_left]]
- [[succ_ne_zero]]
- [[le_zero]]
- [[le_refl]]
- [[le_succ]]
- [[mul_left_cancel_nonzero]]
- [[eq_decidable]]
- [[multiple_decidable_nonzero]]
- [[factor_property_succ]]

## Checked dependents

- [[prime_or_composite]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1925 nodes**, depth **69**.
- Authored script length: **101 commands**.
- Runtime card: `pa lib factor_search_up_to`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

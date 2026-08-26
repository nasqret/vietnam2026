---
title: "Lemma: factor_property_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factor_property_succ`

Extend a bounded prime factor-pair property by checking the new boundary.

## Closed Peano statement

```text
forall B n. (forall c d. (exists k. k + c = B) -> n = c * d -> c = 1 \/ d = 1) -> (forall d. n = S B * d -> S B = 1 \/ d = 1) -> forall c d. (exists k. k + c = S B) -> n = c * d -> c = 1 \/ d = 1
```

## Dependencies

- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]

## Checked dependents

- [[factor_search_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **150 nodes**, depth **20**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib factor_property_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

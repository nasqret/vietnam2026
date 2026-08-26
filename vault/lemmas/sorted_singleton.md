---
title: "Lemma: sorted_singleton"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_singleton`

The fully expanded Sorted predicate holds vacuously on every singleton prefix.

## Closed Peano statement

```text
forall b c. (forall i. (exists h. h + S (S i) = 1) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q))))
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_zero]]
- [[succ_ne_zero]]

## Checked dependents

- [[beta_prefix_extend_sorted_singleton]]
- [[beta_canonical_append_empty]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **65 nodes**, depth **15**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib sorted_singleton`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

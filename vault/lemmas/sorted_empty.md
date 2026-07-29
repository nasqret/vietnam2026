---
title: "Lemma: sorted_empty"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_empty`

The fully expanded Sorted predicate holds vacuously on the empty prefix.

## Closed Peano statement

```text
forall b c. (forall i. (exists h. h + S (S i) = 0) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q))))
```

## Dependencies

- [[le_zero]]
- [[succ_ne_zero]]

## Checked dependents

- [[prime_factorization_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **44 nodes**, depth **14**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib sorted_empty`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: sorted_succ_elim_last"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_succ_elim_last`

Extract the final adjacent ordered pair from a Sorted prefix of length at least two.

## Closed Peano statement

```text
forall b c l. (forall i. (exists h. h + S (S i) = S (S l)) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> exists p q. (((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) /\ (((exists h. h + S q = S ((S S l) * c)) /\ exists w. b = w * S ((S S l) * c) + q) /\ (exists h. h + p = q)))
```

## Dependencies

- [[le_refl]]

## Checked dependents

- [[beta_sorted_factor_le_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **11**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib sorted_succ_elim_last`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

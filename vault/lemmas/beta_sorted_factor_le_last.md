---
title: "Lemma: beta_sorted_factor_le_last"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sorted_factor_le_last`

Every factor in a nonempty adjacent-sorted beta prefix is at most its last factor.

## Closed Peano statement

```text
forall b c l i p q. (exists h. h + S i = S l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) -> ((exists h. h + S q = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + q) -> (forall i. (exists h. h + S S i = S l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> (exists h. h + p = q)
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_zero]]
- [[beta_at_unique]]
- [[le_refl]]
- [[le_eq_or_lt]]
- [[sorted_succ_elim_prefix]]
- [[sorted_succ_elim_last]]
- [[le_trans]]

## Checked dependents

- [[beta_canonical_last_factors_equal]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1587 nodes**, depth **62**.
- Authored script length: **106 commands**.
- Runtime card: `pa lib beta_sorted_factor_le_last`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: sorted_succ_intro"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_succ_intro`

Append one ordered adjacent pair to a nonempty Sorted prefix.

## Closed Peano statement

```text
forall b c l p q. (forall i. (exists h. h + S (S i) = S l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> ((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) -> ((exists h. h + S q = S ((S S l) * c)) /\ exists w. b = w * S ((S S l) * c) + q) -> (exists h. h + p = q) -> (forall i. (exists h. h + S (S i) = S (S l)) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q))))
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[succ_le_succ]]

## Checked dependents

- [[beta_prefix_extend_sorted_succ]]
- [[beta_canonical_append_succ]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **182 nodes**, depth **23**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib sorted_succ_intro`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

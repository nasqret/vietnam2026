---
title: "Lemma: beta_prefix_extend_sorted_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_extend_sorted_succ`

Recode a nonempty Sorted prefix and append a value above its former last value.

## Closed Peano statement

```text
forall l b e s p. (forall i. (exists h. h + S (S i) = S l) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. b = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. b = w * S ((S S i) * e) + q) /\ (exists h. h + p = q)))) -> ((exists h. h + S p = S ((S l) * e)) /\ exists w. b = w * S ((S l) * e) + p) -> (exists h. h + p = s) -> exists z c. ((((exists h. h + S s = S ((S S l) * c)) /\ exists w. z = w * S ((S S l) * c) + s) /\ forall i a. (exists h. h + S i = S l) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. b = w * S ((S i) * e) + a) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + a)) /\ (forall i. (exists h. h + S (S i) = S (S l)) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. z = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[sorted_transport]]
- [[sorted_succ_intro]]
- [[le_refl]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **29414 nodes**, depth **81**.
- Authored script length: **49 commands**.
- Runtime card: `pa lib beta_prefix_extend_sorted_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

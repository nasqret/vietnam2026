---
title: "Lemma: sorted_succ_elim_prefix"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_succ_elim_prefix`

Restrict a Sorted successor prefix to its old prefix.

## Closed Peano statement

```text
forall b c l. (forall i. (exists h. h + S (S i) = S l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> (forall i. (exists h. h + S (S i) = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q))))
```

## Dependencies

- [[le_succ]]

## Checked dependents

- [[beta_sorted_factor_le_last]]
- [[beta_canonical_product_cancel_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **64 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib sorted_succ_elim_prefix`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

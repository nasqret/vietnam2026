---
title: "Lemma: bounded_beta_exclusive_recode_invariant"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_beta_exclusive_recode_invariant`

Fold an empty-based, exclusive beta prefix into another base with append readiness.

## Closed Peano statement

```text
forall N c b e. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> forall k. (exists h. h + k = N) -> exists P z. (~(P = 0) /\ ((forall i. (exists h. h + S i = k) -> exists q. P = S ((S i) * c) * q) /\ ((forall i a. (exists h. h + S i = k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v) /\ forall j. (exists g. g + k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1)))
```

## Dependencies

- [[succ_ne_zero]]
- [[add_eq_zero_right]]
- [[coprime_one_left]]
- [[le_succ_self]]
- [[le_trans]]
- [[beta_exclusive_recode_invariant_step]]

## Checked dependents

- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **19155 nodes**, depth **77**.
- Authored script length: **89 commands**.
- Runtime card: `pa lib bounded_beta_exclusive_recode_invariant`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

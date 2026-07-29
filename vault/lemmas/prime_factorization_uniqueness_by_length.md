---
title: "Lemma: prime_factorization_uniqueness_by_length"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_factorization_uniqueness_by_length`

Strengthened induction on the first canonical factorization length.

## Closed Peano statement

```text
forall l n b c m d e. ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))))) -> ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S m) * v)) /\ exists w. u = w * S ((S m) * v) + n) /\ forall i. (exists h. h + S i = m) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = m) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = m) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. d = w * S ((S S i) * e) + q) /\ (exists h. h + p = q)))))) -> (l = m /\ forall i p q. (exists h. h + S i = l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) -> ((exists h. h + S q = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + q) -> p = q)
```

## Dependencies

- [[beta_product_zero]]
- [[beta_all_prime_product_one_iff_length_zero]]
- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[beta_nonempty_all_prime_product_ne_one]]
- [[nonzero_is_succ]]
- [[beta_canonical_product_cancel_last]]
- [[succ_congr]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[beta_at_unique]]

## Checked dependents

- [[prime_factorization_uniqueness]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29739 nodes**, depth **81**.
- Authored script length: **211 commands**.
- Runtime card: `pa lib prime_factorization_uniqueness_by_length`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

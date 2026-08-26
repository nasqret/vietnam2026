---
title: "Lemma: prime_factorization_exists_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_factorization_exists_up_to`

Bounded induction with one consolidated canonical append dependency.

## Closed Peano statement

```text
forall B n. (exists h. h + n = B) -> ~(n = 0) -> exists l b c. ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q))))))
```

## Dependencies

- [[le_zero]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]
- [[eq_decidable]]
- [[succ_ne_zero]]
- [[beta_at_exists]]
- [[beta_at_self_of_bound]]
- [[beta_at_unique]]
- [[one_mul]]
- [[le_refl]]
- [[add_eq_zero_right]]
- [[all_prime_empty]]
- [[sorted_empty]]
- [[greatest_prime_divisor_descent]]
- [[beta_canonical_append_general]]
- [[mul_comm]]

## Checked dependents

- [[prime_factorization_existence]]

## Verification record

- Independently checked from the empty context.
- Certificate: **43927 nodes**, depth **97**.
- Authored script length: **153 commands**.
- Runtime card: `pa lib prime_factorization_exists_up_to`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

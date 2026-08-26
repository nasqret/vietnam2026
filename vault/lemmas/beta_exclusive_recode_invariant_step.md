---
title: "Lemma: beta_exclusive_recode_invariant_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_exclusive_recode_invariant_step`

Combine modulus-product and cross-base congruence updates for an exclusive prefix.

## Closed Peano statement

```text
forall N c b e k P z. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> (exists h. h + S k = N) -> ~(P = 0) -> (forall i. (exists h. h + S i = k) -> exists q. P = S ((S i) * c) * q) -> (forall i a. (exists h. h + S i = k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v) -> (forall j. (exists g. g + k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> exists z2. (~(P * S ((S k) * c) = 0) /\ ((forall i. (exists h. h + S i = S k) -> exists q. P * S ((S k) * c) = S ((S i) * c) * q) /\ ((forall i a. (exists h. h + S i = S k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> exists u v. z2 + S ((S i) * c) * u = a + S ((S i) * c) * v) /\ forall j. (exists g. g + S k = j) -> (exists h. h + j = N) -> forall d. (exists u. P * S ((S k) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1)))
```

## Dependencies

- [[beta_exclusive_accumulated_product_step]]
- [[beta_exclusive_recode_congruence_step]]

## Checked dependents

- [[bounded_beta_exclusive_recode_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **18709 nodes**, depth **71**.
- Authored script length: **49 commands**.
- Runtime card: `pa lib beta_exclusive_recode_invariant_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: beta_accumulated_product_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_accumulated_product_step`

Extend the accumulated beta-modulus product invariant by one bounded position.

## Closed Peano statement

```text
forall N c k P. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> (exists h. h + S k = N) -> ~(P = 0) -> (forall i. (exists h. h + i = k) -> exists q. P = S ((S i) * c) * q) -> (forall j. (exists g. g + S k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> (~(P * S ((S (S k)) * c) = 0) /\ ((forall i. (exists h. h + i = S k) -> exists q. P * S ((S (S k)) * c) = S ((S i) * c) * q) /\ forall j. (exists g. g + S (S k) = j) -> (exists h. h + j = N) -> forall d. (exists u. P * S ((S (S k)) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1))
```

## Dependencies

- [[mul_ne_zero]]
- [[right_factor_divides_product]]
- [[beta_modulus_nonzero]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]
- [[multiple_mul_right]]
- [[le_succ_self]]
- [[lt_of_le_of_lt]]
- [[lt_irrefl_expanded]]
- [[beta_moduli_pairwise_coprime_bounded]]
- [[coprime_mul_left]]

## Checked dependents

- [[beta_crt_prefix_invariant_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **11174 nodes**, depth **69**.
- Authored script length: **90 commands**.
- Runtime card: `pa lib beta_accumulated_product_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

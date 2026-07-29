---
title: "Lemma: beta_exclusive_accumulated_product_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_exclusive_accumulated_product_step`

Extend the accumulated target-modulus product for an exclusive prefix.

## Closed Peano statement

```text
forall N c k P. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> (exists h. h + S k = N) -> ~(P = 0) -> (forall i. (exists h. h + S i = k) -> exists q. P = S ((S i) * c) * q) -> (forall j. (exists g. g + k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> (~(P * S ((S k) * c) = 0) /\ ((forall i. (exists h. h + S i = S k) -> exists q. P * S ((S k) * c) = S ((S i) * c) * q) /\ forall j. (exists g. g + S k = j) -> (exists h. h + j = N) -> forall d. (exists u. P * S ((S k) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1))
```

## Dependencies

- [[mul_ne_zero]]
- [[right_factor_divides_product]]
- [[beta_modulus_nonzero]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[multiple_mul_right]]
- [[le_succ_self]]
- [[le_trans]]
- [[lt_to_le]]
- [[lt_irrefl_expanded]]
- [[beta_moduli_pairwise_coprime_bounded]]
- [[coprime_mul_left]]

## Checked dependents

- [[beta_exclusive_recode_invariant_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **11222 nodes**, depth **70**.
- Authored script length: **95 commands**.
- Runtime card: `pa lib beta_exclusive_accumulated_product_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: beta_factor_divides_product"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_factor_divides_product`

Every decoded factor inside an exact beta Product divides its terminal product.

## Closed Peano statement

```text
forall b c l n i p. (exists h. h + S i = l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> exists q. n = p * q
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[beta_product_succ_decompose]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[beta_at_unique]]
- [[mul_comm]]
- [[multiple_mul_right]]

## Checked dependents

- [[beta_canonical_append_general]]
- [[beta_canonical_last_factor_bound]]
- [[beta_nonempty_all_prime_product_ne_one]]
- [[beta_canonical_last_factors_equal]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2970 nodes**, depth **65**.
- Authored script length: **82 commands**.
- Runtime card: `pa lib beta_factor_divides_product`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

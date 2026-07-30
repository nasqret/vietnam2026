---
title: "Lemma: beta_product_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_zero`

The product of an empty decoded prefix is one.

## Closed Peano statement

```text
forall b c n. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + n) /\ forall i. (exists h. h + S i = 0) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> n = 1
```

## Dependencies

- [[beta_at_unique]]

## Checked dependents

- [[beta_prime_divisor_product_member]]
- [[beta_all_prime_product_one_iff_length_zero]]
- [[prime_factorization_uniqueness_by_length]]
- [[pow_zero]]
- [[beta_product_pointwise_mod_congruent]]
- [[factorial_zero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1171 nodes**, depth **60**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib beta_product_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

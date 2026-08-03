---
title: "Lemma: beta_product_succ_decompose"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_succ_decompose`

A successor product decomposes into its prefix product and final decoded factor.

## Closed Peano statement

```text
forall b c l n. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S l) * v)) /\ exists q. u = q * S ((S S l) * v) + n) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> exists p r. (((exists h. h + S p = S ((S l) * c)) /\ exists q. b = q * S ((S l) * c) + p) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S r = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + r) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) /\ n = r * p))
```

## Dependencies

- [[le_refl]]
- [[le_succ]]
- [[beta_at_unique]]

## Checked dependents

- [[beta_factor_divides_product]]
- [[beta_prime_divisor_product_member]]
- [[beta_canonical_product_cancel_last]]
- [[pow_successor_decompose]]
- [[beta_product_pointwise_mod_congruent]]
- [[factorial_succ_decompose]]
- [[beta_product_replace_balance]]
- [[beta_product_swap_last_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1257 nodes**, depth **62**.
- Authored script length: **51 commands**.
- Runtime card: `pa lib beta_product_succ_decompose`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

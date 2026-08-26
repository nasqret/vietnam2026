---
title: "Lemma: beta_prime_divisor_product_member"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prime_divisor_product_member`

A prime divisor of an AllPrime beta Product occurs as one of its decoded factors.

## Closed Peano statement

```text
forall b c l n p. (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) -> (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> (exists k. n = p * k) -> exists i. ((exists h. h + S i = l) /\ ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p))
```

## Dependencies

- [[beta_product_zero]]
- [[divisor_one]]
- [[beta_product_succ_decompose]]
- [[all_prime_succ_elim_prefix]]
- [[all_prime_succ_elim_last]]
- [[euclid_prime_dvd_product]]
- [[prime_divisor_eq_one_or_self]]
- [[beta_at_unique]]
- [[le_succ]]
- [[le_refl]]

## Checked dependents

- [[beta_canonical_last_factors_equal]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9499 nodes**, depth **67**.
- Authored script length: **114 commands**.
- Runtime card: `pa lib beta_prime_divisor_product_member`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

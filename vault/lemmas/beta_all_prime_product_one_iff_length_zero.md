---
title: "Lemma: beta_all_prime_product_one_iff_length_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_all_prime_product_one_iff_length_zero`

Under AllPrime, a beta Product is one exactly when its encoded factor length is zero.

## Closed Peano statement

```text
forall b c l n. (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> ((n = 1 -> l = 0) /\ (l = 0 -> n = 1))
```

## Dependencies

- [[beta_product_zero]]
- [[beta_nonempty_all_prime_product_ne_one]]
- [[succ_ne_zero]]

## Checked dependents

- [[prime_factorization_uniqueness_by_length]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4506 nodes**, depth **69**.
- Authored script length: **34 commands**.
- Runtime card: `pa lib beta_all_prime_product_one_iff_length_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

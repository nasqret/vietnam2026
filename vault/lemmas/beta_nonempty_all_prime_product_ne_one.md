---
title: "Lemma: beta_nonempty_all_prime_product_ne_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_nonempty_all_prime_product_ne_one`

A nonempty product of prime decoded factors cannot have terminal value one.

## Closed Peano statement

```text
forall b c l n. (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S l) * v)) /\ exists w. u = w * S ((S S l) * v) + n) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> ~(n = 1)
```

## Dependencies

- [[all_prime_succ_elim_last]]
- [[beta_factor_divides_product]]
- [[le_refl]]
- [[divisor_one]]

## Checked dependents

- [[beta_all_prime_product_one_iff_length_zero]]
- [[prime_factorization_uniqueness_by_length]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3266 nodes**, depth **67**.
- Authored script length: **35 commands**.
- Runtime card: `pa lib beta_nonempty_all_prime_product_ne_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

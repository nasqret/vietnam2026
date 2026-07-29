---
title: "Lemma: beta_canonical_last_factors_equal"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_canonical_last_factors_equal`

Two nonempty sorted AllPrime Products of the same number have equal last factors.

## Closed Peano statement

```text
forall b c z e l k n p q. (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i. (exists h. h + S S i = S l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S l) * v)) /\ exists w. u = w * S ((S S l) * v) + n) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> ((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) -> (forall i. (exists h. h + S i = S k) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i. (exists h. h + S S i = S k) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. z = w * S ((S S i) * e) + q) /\ (exists h. h + p = q)))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S k) * v)) /\ exists w. u = w * S ((S S k) * v) + n) /\ forall i. (exists h. h + S i = S k) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> ((exists h. h + S q = S ((S k) * e)) /\ exists w. z = w * S ((S k) * e) + q) -> p = q
```

## Dependencies

- [[all_prime_succ_elim_last]]
- [[beta_at_unique]]
- [[beta_factor_divides_product]]
- [[le_refl]]
- [[beta_prime_divisor_product_member]]
- [[beta_sorted_factor_le_last]]
- [[le_antisymm]]

## Checked dependents

- [[beta_canonical_product_cancel_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **15648 nodes**, depth **72**.
- Authored script length: **138 commands**.
- Runtime card: `pa lib beta_canonical_last_factors_equal`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

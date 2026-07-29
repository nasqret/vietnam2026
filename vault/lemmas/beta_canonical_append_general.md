---
title: "Lemma: beta_canonical_append_general"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_canonical_append_general`

Append one prime to any canonical prefix using one shared beta append certificate.

## Closed Peano statement

```text
forall l b c n s. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i. (exists h. h + S S i = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> (~(s = 1) /\ forall a d. s = a * d -> a = 1 \/ d = 1) -> (forall r. (~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) -> (exists k. n = r * k) -> (exists h. h + r = s)) -> exists z e. (((exists h. h + S s = S ((S l) * e)) /\ exists w. z = w * S ((S l) * e) + s) /\ ((forall i a. (exists h. h + S i = l) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + a) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + a)) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S (n * s) = S ((S S l) * v)) /\ exists w. u = w * S ((S S l) * v) + (n * s)) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = S l) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. z = w * S ((S S i) * e) + q) /\ (exists h. h + p = q))))))))
```

## Dependencies

- [[beta_factor_prefix_product_append]]
- [[all_prime_transport]]
- [[all_prime_succ_intro]]
- [[zero_or_succ]]
- [[sorted_singleton]]
- [[sorted_transport]]
- [[all_prime_succ_elim_last]]
- [[beta_factor_divides_product]]
- [[le_refl]]
- [[sorted_succ_intro]]

## Checked dependents

- [[prime_factorization_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **33165 nodes**, depth **82**.
- Authored script length: **126 commands**.
- Runtime card: `pa lib beta_canonical_append_general`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

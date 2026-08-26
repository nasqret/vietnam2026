---
title: "Lemma: beta_canonical_append_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_canonical_append_succ`

Append one ordered prime using the canonical shared-code factor/Product append helper.

## Closed Peano statement

```text
forall l b c n s p. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S l) * v)) /\ exists w. u = w * S ((S S l) * v) + n) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i. (exists h. h + S (S i) = S l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> ((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) -> (exists h. h + p = s) -> (~(s = 1) /\ forall a d. s = a * d -> a = 1 \/ d = 1) -> exists z e. (((exists h. h + S s = S ((S S l) * e)) /\ exists w. z = w * S ((S S l) * e) + s) /\ ((forall i a. (exists h. h + S i = S l) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + a) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + a)) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S (n * s) = S ((S S (S l)) * v)) /\ exists w. u = w * S ((S S (S l)) * v) + (n * s)) /\ forall i. (exists h. h + S i = S (S l)) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = S (S l)) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S (S i) = S (S l)) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. z = w * S ((S S i) * e) + q) /\ (exists h. h + p = q))))))))
```

## Dependencies

- [[beta_factor_prefix_product_append]]
- [[all_prime_transport]]
- [[all_prime_succ_intro]]
- [[sorted_transport]]
- [[sorted_succ_intro]]
- [[le_refl]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **30020 nodes**, depth **82**.
- Authored script length: **81 commands**.
- Runtime card: `pa lib beta_canonical_append_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

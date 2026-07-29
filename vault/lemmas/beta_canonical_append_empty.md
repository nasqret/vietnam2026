---
title: "Lemma: beta_canonical_append_empty"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_canonical_append_empty`

Append the first prime using the canonical shared-code factor/Product append helper.

## Closed Peano statement

```text
forall b c s. (~(s = 1) /\ forall a d. s = a * d -> a = 1 \/ d = 1) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ forall i. (exists h. h + S i = 0) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) -> exists z e. (((exists h. h + S s = S ((S 0) * e)) /\ exists w. z = w * S ((S 0) * e) + s) /\ ((forall i a. (exists h. h + S i = 0) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + a) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + a)) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S s = S ((S 1) * v)) /\ exists w. u = w * S ((S 1) * v) + s) /\ forall i. (exists h. h + S i = 1) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = 1) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S (S i) = 1) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. z = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. z = w * S ((S S i) * e) + q) /\ (exists h. h + p = q))))))))
```

## Dependencies

- [[beta_factor_prefix_product_append]]
- [[all_prime_empty]]
- [[all_prime_succ_intro]]
- [[sorted_singleton]]
- [[one_mul]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **29783 nodes**, depth **82**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib beta_canonical_append_empty`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

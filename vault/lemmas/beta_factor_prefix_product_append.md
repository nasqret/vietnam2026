---
title: "Lemma: beta_factor_prefix_product_append"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_factor_prefix_product_append`

Extend a factor prefix by p and simultaneously append p to its exact Product.

## Closed Peano statement

```text
forall b c l r p. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S r = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + r) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> exists z e. (((exists h. h + S p = S ((S l) * e)) /\ exists q. z = q * S ((S l) * e) + p) /\ ((forall i a. (exists h. h + S i = l) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. z = q * S ((S i) * e) + a)) /\ (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S (r * p) = S ((S S l) * v)) /\ exists q. u = q * S ((S S l) * v) + (r * p)) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists q. z = q * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p))))))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[beta_product_transport_prefix]]
- [[zero_le]]
- [[succ_le_succ]]
- [[le_refl]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- [[beta_canonical_append_empty]]
- [[beta_canonical_append_succ]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29447 nodes**, depth **81**.
- Authored script length: **125 commands**.
- Runtime card: `pa lib beta_factor_prefix_product_append`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

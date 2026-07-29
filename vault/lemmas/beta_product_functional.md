---
title: "Lemma: beta_product_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_functional`

The fully expanded beta-coded Product relation is functional in its terminal product.

## Closed Peano statement

```text
forall b c l n u v m w d. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p))))) -> (((exists h. h + S 1 = S ((S 0) * d)) /\ exists q. w = q * S ((S 0) * d) + 1) /\ (((exists h. h + S m = S ((S l) * d)) /\ exists q. w = q * S ((S l) * d) + m) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * d)) /\ exists q. w = q * S ((S i) * d) + r) /\ (((exists h. h + S s = S ((S S i) * d)) /\ exists q. w = q * S ((S S i) * d) + s) /\ s = r * p))))) -> n = m
```

## Dependencies

- [[beta_at_unique]]
- [[le_refl]]
- [[le_succ]]
- [[mul_congr]]

## Checked dependents

- [[beta_product_exists_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1382 nodes**, depth **60**.
- Authored script length: **153 commands**.
- Runtime card: `pa lib beta_product_functional`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

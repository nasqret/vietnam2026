---
title: "Lemma: beta_product_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_exists_unique`

Every finite decoded beta prefix has exactly one relational product value.

## Closed Peano statement

```text
forall b c l. exists n. ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) /\ forall m. (exists w d. (((exists h. h + S 1 = S ((S 0) * d)) /\ exists q. w = q * S ((S 0) * d) + 1) /\ (((exists h. h + S m = S ((S l) * d)) /\ exists q. w = q * S ((S l) * d) + m) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * d)) /\ exists q. w = q * S ((S i) * d) + r) /\ (((exists h. h + S s = S ((S S i) * d)) /\ exists q. w = q * S ((S S i) * d) + s) /\ s = r * p)))))) -> n = m)
```

## Dependencies

- [[beta_product_exists]]
- [[beta_product_functional]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **31908 nodes**, depth **87**.
- Authored script length: **32 commands**.
- Runtime card: `pa lib beta_product_exists_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

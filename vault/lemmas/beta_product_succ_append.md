---
title: "Lemma: beta_product_succ_append"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_succ_append`

Append one decoded factor to an existing fully expanded Product witness.

## Closed Peano statement

```text
forall b c l r p. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S r = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + r) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> ((exists h. h + S p = S ((S l) * c)) /\ exists q. b = q * S ((S l) * c) + p) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S (r * p) = S ((S S l) * v)) /\ exists q. u = q * S ((S S l) * v) + (r * p)) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p))))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[zero_le]]
- [[succ_le_succ]]
- [[le_refl]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **29360 nodes**, depth **81**.
- Authored script length: **101 commands**.
- Runtime card: `pa lib beta_product_succ_append`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

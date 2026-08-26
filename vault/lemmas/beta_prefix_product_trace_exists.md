---
title: "Lemma: beta_prefix_product_trace_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_product_trace_exists`

Every decoded beta factor prefix admits a beta-coded exact prefix-product trace.

## Closed Peano statement

```text
forall b c l. exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S (S i)) * v)) /\ exists q. u = q * S ((S (S i)) * v) + s) /\ s = r * p))))
```

## Dependencies

- [[beta_at_self_of_bound]]
- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[beta_at_exists]]
- [[beta_prefix_extend]]
- [[zero_le]]
- [[succ_le_succ]]
- [[le_refl]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[one_mul]]

## Checked dependents

- [[beta_product_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29981 nodes**, depth **85**.
- Authored script length: **133 commands**.
- Runtime card: `pa lib beta_prefix_product_trace_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

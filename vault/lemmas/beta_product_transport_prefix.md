---
title: "Lemma: beta_product_transport_prefix"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_transport_prefix`

One-way extensional factor-prefix preservation transports Product without changing its trace.

## Closed Peano statement

```text
forall b c z e l n. (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> (forall i a. (exists h. h + S i = l) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. z = q * S ((S i) * e) + a)) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists q. z = q * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p))))))
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_factor_prefix_product_append]]
- [[pow_functional]]
- [[factorial_functional]]
- [[beta_product_replace_balance]]

## Verification record

- Independently checked from the empty context.
- Certificate: **59 nodes**, depth **29**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib beta_product_transport_prefix`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

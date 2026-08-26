---
title: "Lemma: beta_product_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_exists`

Every finite decoded beta prefix has an exact relational product and a coded trace.

## Closed Peano statement

```text
forall b c l. exists n u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S (S i)) * v)) /\ exists q. u = q * S ((S (S i)) * v) + s) /\ s = r * p)))))
```

## Dependencies

- [[beta_prefix_product_trace_exists]]
- [[beta_at_exists]]

## Checked dependents

- [[beta_product_exists_unique]]
- [[pow_exists]]
- [[factorial_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **30487 nodes**, depth **86**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib beta_product_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_mul"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_mul`

Balanced natural congruence respects multiplication.

## Closed Peano statement

```text
forall m a b c d. (exists u v. a + m * u = b + m * v) -> (exists r s. c + m * r = d + m * s) -> exists x y. (a * c) + m * x = (b * d) + m * y
```

## Dependencies

- [[mod_eq_mul_right]]
- [[mod_eq_mul_left]]
- [[mod_eq_trans]]

## Checked dependents

- [[beta_product_pointwise_mod_congruent]]
- [[pow_mod_congruent]]
- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1505 nodes**, depth **32**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib mod_eq_mul`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

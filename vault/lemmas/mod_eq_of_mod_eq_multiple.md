---
title: "Lemma: mod_eq_of_mod_eq_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_of_mod_eq_multiple`

Balanced congruence descends from a multiple modulus to every divisor modulus.

## Closed Peano statement

```text
forall m P x a. (exists k. P = m * k) -> (exists u v. x + P * u = a + P * v) -> exists r s. x + m * r = a + m * s
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- [[binary_crt_fold_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **157 nodes**, depth **23**.
- Authored script length: **23 commands**.
- Runtime card: `pa lib mod_eq_of_mod_eq_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

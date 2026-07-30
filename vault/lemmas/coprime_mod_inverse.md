---
title: "Lemma: coprime_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_mod_inverse`

A nonzero modulus turns balanced Bezout data into a natural modular inverse.

## Closed Peano statement

```text
forall a m. ~(m = 0) -> (forall d. (exists x. a = d * x) -> (exists y. m = d * y) -> d = 1) -> exists z u v. a * z + m * u = 1 + m * v
```

## Dependencies

- [[nonzero_is_succ]]
- [[coprime_balanced_mod_inverse]]
- [[mod_eq_refl]]
- [[mod_eq_add]]
- [[mod_eq_predecessor_cancel]]
- [[mod_eq_trans]]
- [[mul_add]]
- [[mul_assoc]]
- [[mul_comm]]

## Checked dependents

- [[mod_eq_cancel_coprime]]
- [[prime_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3820 nodes**, depth **51**.
- Authored script length: **66 commands**.
- Runtime card: `pa lib coprime_mod_inverse`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_cancel_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_cancel_coprime`

A coprime factor cancels from balanced congruence at nonzero modulus.

## Closed Peano statement

```text
forall m a x y. ~(m = 0) -> (forall d. (exists x. a = d * x) -> (exists y. m = d * y) -> d = 1) -> (exists u v. (a * x) + m * u = (a * y) + m * v) -> exists r s. x + m * r = y + m * s
```

## Dependencies

- [[coprime_mod_inverse]]
- [[mod_eq_mul_right]]
- [[mod_eq_mul_left]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mul_assoc]]
- [[mul_comm]]
- [[mul_one]]

## Checked dependents

- [[prime_mod_cancel]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5804 nodes**, depth **52**.
- Authored script length: **114 commands**.
- Runtime card: `pa lib mod_eq_cancel_coprime`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

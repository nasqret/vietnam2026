---
title: "Lemma: binary_crt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `binary_crt`

Constructive binary CRT for positive coprime natural moduli using balanced congruence.

## Closed Peano statement

```text
forall m n a b. ~(m = 0) -> ~(n = 0) -> (forall d. (exists u. m = d * u) -> (exists v. n = d * v) -> d = 1) -> exists x. (exists u v. x + m * u = a + m * v) /\ (exists r s. x + n * r = b + n * s)
```

## Dependencies

- [[nonzero_is_succ]]
- [[coprime_balanced_bezout]]
- [[bezout_mod_left]]
- [[bezout_mod_right]]
- [[mod_eq_mul_left]]
- [[mul_add]]
- [[mul_one]]
- [[dvd_to_mod_zero]]
- [[mul_assoc]]
- [[mul_comm]]
- [[mod_eq_add]]
- [[mod_eq_refl]]
- [[mod_eq_trans]]
- [[mod_eq_predecessor_cancel]]
- [[zero_add]]

## Checked dependents

- [[binary_crt_remainders]]
- [[binary_crt_beta_pair]]
- [[binary_crt_fold_step]]
- [[crt_scaled_common_remainder_lift]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5044 nodes**, depth **51**.
- Authored script length: **276 commands**.
- Runtime card: `pa lib binary_crt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

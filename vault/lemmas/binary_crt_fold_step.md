---
title: "Lemma: binary_crt_fold_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `binary_crt_fold_step`

One binary CRT extension preserves every old congruence whose modulus divides the accumulated product.

## Closed Peano statement

```text
forall P n x b. ~(P = 0) -> ~(n = 0) -> (forall d. (exists u. P = d * u) -> (exists v. n = d * v) -> d = 1) -> exists z. ((forall m a. (exists k. P = m * k) -> (exists u v. x + m * u = a + m * v) -> exists r s. z + m * r = a + m * s) /\ exists q r. z + n * q = b + n * r)
```

## Dependencies

- [[binary_crt]]
- [[mod_eq_of_mod_eq_multiple]]
- [[mod_eq_trans]]

## Checked dependents

- [[beta_crt_prefix_congruence_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5501 nodes**, depth **52**.
- Authored script length: **40 commands**.
- Runtime card: `pa lib binary_crt_fold_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

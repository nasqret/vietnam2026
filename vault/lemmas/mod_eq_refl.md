---
title: "Lemma: mod_eq_refl"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_refl`

Balanced natural congruence is reflexive.

## Closed Peano statement

```text
forall m a. exists u v. a + m * u = a + m * v
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[binary_crt]]
- [[beta_product_pointwise_mod_congruent]]
- [[beta_sum_pointwise_mod_congruent]]
- [[coprime_mod_inverse]]
- [[pow_mod_congruent]]
- [[pow_predecessor_parity_mod]]
- [[crt_scaled_common_remainder_lift]]
- [[generalized_binary_crt_sufficient_zero_left]]
- [[generalized_binary_crt_sufficient_zero_right]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5 nodes**, depth **5**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib mod_eq_refl`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_trans`

Balanced natural congruence is transitive.

## Closed Peano statement

```text
forall m a b c. (exists u v. a + m * u = b + m * v) -> (exists r s. b + m * r = c + m * s) -> exists x y. a + m * x = c + m * y
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]
- [[mul_add]]

## Checked dependents

- [[mod_eq_mul]]
- [[mod_eq_to_remainder_decomposition]]
- [[binary_crt]]
- [[binary_crt_fold_step]]
- [[mod_eq_decidable_from_remainders]]
- [[quadratic_residue_bounded_equiv]]
- [[coprime_mod_inverse]]
- [[mod_eq_cancel_coprime]]
- [[bounded_square_mod3_classify]]
- [[bounded_square_mod5_classify]]
- [[bounded_square_mod7_classify]]
- [[pow_predecessor_parity_mod]]
- [[prime_bounded_nonzero_mod_inverse]]
- [[canonical_remainders_characterize_mod_eq]]
- [[bounded_mod_inverse_unique]]
- [[coprime_bounded_mod_inverse]]
- [[crt_solution_pair_congruent]]
- [[crt_common_solution_implies_gcd_compatible]]
- [[mod_eq_common_remainder_decomposition]]
- [[crt_solution_class_iff_lcm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **252 nodes**, depth **29**.
- Authored script length: **42 commands**.
- Runtime card: `pa lib mod_eq_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

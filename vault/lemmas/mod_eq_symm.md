---
title: "Lemma: mod_eq_symm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_symm`

Balanced natural congruence is symmetric.

## Closed Peano statement

```text
forall m a b. (exists u v. a + m * u = b + m * v) -> exists r s. b + m * r = a + m * s
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mod_eq_decidable_from_remainders]]
- [[quadratic_residue_bounded_equiv]]
- [[mod_eq_cancel_coprime]]
- [[prime_bounded_nonzero_mod_inverse]]
- [[canonical_remainders_characterize_mod_eq]]
- [[bounded_mod_inverse_unique]]
- [[coprime_bounded_mod_inverse]]
- [[crt_solution_pair_congruent]]
- [[crt_common_solution_implies_gcd_compatible]]
- [[mod_eq_common_remainder_decomposition]]
- [[generalized_binary_crt_sufficient_zero_right]]
- [[mod_eq_lcm_merge]]
- [[crt_solution_canonical_remainder_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **12 nodes**, depth **10**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib mod_eq_symm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

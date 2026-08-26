---
title: "Lemma: le_refl"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_refl`

The defined order is reflexive; zero is its witness.

## Closed Peano statement

```text
forall n. n <= n
```

## Dependencies

- [[zero_add]]

## Checked dependents

- [[gcd_exists_relational]]
- [[gcd_balanced_bezout_exists]]
- [[factor_search_up_to]]
- [[prime_divisor_exists]]
- [[beta_crt_prefix_congruence_step]]
- [[bounded_beta_crt_for_existing_code]]
- [[beta_exclusive_recode_congruence_step]]
- [[beta_prefix_extend]]
- [[beta_prefix_product_trace_exists]]
- [[beta_product_functional]]
- [[beta_product_succ_decompose]]
- [[beta_product_succ_append]]
- [[beta_factor_prefix_product_append]]
- [[all_prime_succ_elim_last]]
- [[sorted_succ_elim_last]]
- [[beta_prefix_extend_sorted_succ]]
- [[beta_canonical_append_succ]]
- [[greatest_prime_divisor_search]]
- [[beta_canonical_append_general]]
- [[beta_canonical_last_factor_bound]]
- [[prime_factorization_exists_up_to]]
- [[prime_factorization_existence]]
- [[beta_prime_divisor_product_member]]
- [[beta_sorted_factor_le_last]]
- [[beta_nonempty_all_prime_product_ne_one]]
- [[beta_canonical_last_factors_equal]]
- [[pow_successor_decompose]]
- [[beta_prefix_sum_trace_exists]]
- [[beta_sum_trace_functional]]
- [[beta_sum_succ_decompose]]
- [[beta_product_pointwise_mod_congruent]]
- [[beta_sum_pointwise_mod_congruent]]
- [[all_bits_last_succ]]
- [[factorial_succ_decompose]]
- [[beta_prefix_swap_last_from_entries]]
- [[finite_swap_last_bounded]]
- [[finite_swap_last_injective]]
- [[finite_swap_last_surjective_back]]
- [[finite_contains_decidable]]
- [[finite_bounded_last_succ]]
- [[finite_surjective_succ_intro]]
- [[finite_last_is_top_from_prefix_surjective]]
- [[finite_bounded_injective_surjective]]
- [[beta_product_replace_balance]]
- [[beta_product_swap_last_invariant]]
- [[finite_fixed_last_prefix_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **25 nodes**, depth **9**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib le_refl`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

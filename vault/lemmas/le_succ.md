---
title: "Lemma: le_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_succ`

A weak inequality remains true after raising its upper bound by one.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) -> exists r. r + a = S b
```

## Dependencies

- [[add_succ_left]]

## Checked dependents

- [[factor_search_up_to]]
- [[base_le_beta_modulus]]
- [[beta_product_functional]]
- [[beta_product_succ_decompose]]
- [[all_prime_succ_elim_prefix]]
- [[sorted_succ_elim_prefix]]
- [[greatest_prime_divisor_search]]
- [[beta_prime_divisor_product_member]]
- [[pow_successor_decompose]]
- [[beta_sum_trace_functional]]
- [[beta_sum_succ_decompose]]
- [[beta_product_pointwise_mod_congruent]]
- [[beta_sum_pointwise_mod_congruent]]
- [[all_bits_prefix_succ]]
- [[factorial_succ_decompose]]
- [[finite_injective_prefix_succ]]
- [[beta_prefix_swap_last_from_entries]]
- [[finite_swap_last_bounded]]
- [[finite_swap_last_injective]]
- [[finite_swap_last_surjective_back]]
- [[finite_contains_decidable]]
- [[finite_bounded_prefix_without_top]]
- [[finite_surjective_succ_intro]]
- [[finite_last_is_top_from_prefix_surjective]]
- [[finite_bounded_injective_surjective]]
- [[beta_product_replace_balance]]
- [[beta_product_swap_last_invariant]]
- [[finite_fixed_last_prefix_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **40 nodes**, depth **11**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

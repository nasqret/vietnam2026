---
title: "Lemma: succ_ne_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `succ_ne_zero`

No successor is zero (the reusable PA1 lemma).

## Closed Peano statement

```text
forall n. ~(S n = 0)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_left_cancel_nonzero]]
- [[factor_search_up_to]]
- [[prime_nonzero]]
- [[beta_modulus_nonzero]]
- [[bounded_common_multiple_step]]
- [[bounded_common_multiple_exists]]
- [[bounded_beta_exclusive_recode_invariant]]
- [[beta_prefix_product_trace_exists]]
- [[all_prime_empty]]
- [[sorted_empty]]
- [[sorted_singleton]]
- [[beta_factor_divides_product]]
- [[prime_factorization_exists_up_to]]
- [[beta_all_prime_product_one_iff_length_zero]]
- [[prime_factorization_uniqueness_by_length]]
- [[beta_repeat_empty]]
- [[beta_range_empty]]
- [[beta_prefix_sum_trace_exists]]
- [[all_bits_zero]]
- [[qres_mod3_canonical_iff]]
- [[qres_mod5_canonical_iff]]
- [[qres_mod7_canonical_iff]]
- [[finite_surjective_zero]]
- [[beta_prefix_replace_exists]]
- [[finite_contains_decidable]]
- [[beta_product_replace_balance]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1 nodes**, depth **1**.
- Authored script length: **1 commands**.
- Runtime card: `pa lib succ_ne_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

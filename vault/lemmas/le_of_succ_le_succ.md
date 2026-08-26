---
title: "Lemma: le_of_succ_le_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_of_succ_le_succ`

Successor order reflects to the underlying naturals.

## Closed Peano statement

```text
forall a b. (exists k. k + S a = S b) -> exists r. r + a = b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[gcd_exists_up_to]]
- [[gcd_balanced_bezout_exists_up_to]]
- [[factor_property_succ]]
- [[prime_divisor_exists_up_to]]
- [[beta_accumulated_product_step]]
- [[beta_crt_prefix_congruence_step]]
- [[beta_exclusive_accumulated_product_step]]
- [[beta_exclusive_recode_congruence_step]]
- [[beta_prefix_product_trace_exists]]
- [[beta_product_succ_append]]
- [[beta_factor_prefix_product_append]]
- [[all_prime_succ_intro]]
- [[sorted_singleton]]
- [[sorted_succ_intro]]
- [[greatest_prime_divisor_search]]
- [[beta_factor_divides_product]]
- [[prime_factorization_exists_up_to]]
- [[beta_sorted_factor_le_last]]
- [[prime_factorization_uniqueness_by_length]]
- [[beta_repeat_succ_extend]]
- [[beta_range_succ_extend]]
- [[beta_prefix_sum_trace_exists]]
- [[lt_three_cases]]
- [[lt_five_cases]]
- [[lt_seven_cases]]
- [[finite_lt_succ_eq_or_lt]]

## Verification record

- Independently checked from the empty context.
- Certificate: **16 nodes**, depth **11**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib le_of_succ_le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: add_eq_zero_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_eq_zero_right`

A sum equal to zero has zero as its right addend.

## Closed Peano statement

```text
forall a b. a + b = 0 -> b = 0
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_eq_zero]]
- [[le_zero]]
- [[add_eq_zero_left]]
- [[add_eq_zero_components]]
- [[mul_eq_one_components]]
- [[factor_difference]]
- [[bounded_beta_exclusive_recode_invariant]]
- [[beta_prefix_product_trace_exists]]
- [[all_prime_empty]]
- [[beta_factor_divides_product]]
- [[prime_factorization_exists_up_to]]
- [[prime_factorization_uniqueness_by_length]]

## Verification record

- Independently checked from the empty context.
- Certificate: **19 nodes**, depth **12**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib add_eq_zero_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

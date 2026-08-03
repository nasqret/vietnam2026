---
title: "Lemma: one_mul"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `one_mul`

One is a left identity for multiplication.

## Closed Peano statement

```text
forall n. 1 * n = n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_eq_one_components]]
- [[one_multiple]]
- [[coprime_to_is_gcd_one]]
- [[gauss_coprime_cancel]]
- [[le_scaled_nonzero]]
- [[beta_prefix_product_trace_exists]]
- [[beta_canonical_append_empty]]
- [[prime_factorization_exists_up_to]]
- [[beta_prefix_sum_trace_exists]]
- [[pow_one_from_zero_successor]]
- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **26 nodes**, depth **9**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib one_mul`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

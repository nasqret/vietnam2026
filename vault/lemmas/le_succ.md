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

## Verification record

- Independently checked from the empty context.
- Certificate: **40 nodes**, depth **11**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: beta_at_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_unique`

The decoded residue at a Gödel-beta position is unique.

## Closed Peano statement

```text
forall b c i x y. ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x) -> ((exists h. h + S y = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + y) -> x = y
```

## Dependencies

- [[mul_comm]]
- [[division_remainder_unique]]

## Checked dependents

- [[beta_at_exists_unique]]
- [[beta_crt_prefix_congruence_step]]
- [[beta_exclusive_recode_congruence_step]]
- [[beta_product_functional]]
- [[beta_product_zero]]
- [[beta_product_succ_decompose]]
- [[beta_factor_divides_product]]
- [[prime_factorization_exists_up_to]]
- [[beta_prime_divisor_product_member]]
- [[beta_sorted_factor_le_last]]
- [[beta_canonical_last_factors_equal]]
- [[beta_canonical_product_cancel_last]]
- [[prime_factorization_uniqueness_by_length]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1121 nodes**, depth **59**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib beta_at_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

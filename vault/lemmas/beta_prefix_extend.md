---
title: "Lemma: beta_prefix_extend"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_extend`

Rebase an arbitrary decoded prefix and append one exact natural value.

## Closed Peano statement

```text
forall k b e s. exists z c. (((exists h. h + S s = S ((S k) * c)) /\ exists q. z = q * S ((S k) * c) + s) /\ forall i a. (exists h. h + S i = k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. z = q * S ((S i) * c) + a))
```

## Dependencies

- [[bounded_common_multiple_exists]]
- [[scaled_bounded_common_multiple]]
- [[bounded_beta_exclusive_recode_invariant]]
- [[le_refl]]
- [[beta_modulus_nonzero]]
- [[binary_crt_fold_step]]
- [[new_value_lt_scaled_base]]
- [[beta_value_lt_scaled_base]]
- [[beta_at_of_mod_eq_bound]]

## Checked dependents

- [[beta_prefix_product_trace_exists]]
- [[beta_product_succ_append]]
- [[beta_factor_prefix_product_append]]
- [[beta_prefix_extend_all_prime]]
- [[beta_prefix_extend_sorted_singleton]]
- [[beta_prefix_extend_sorted_succ]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29057 nodes**, depth **80**.
- Authored script length: **105 commands**.
- Runtime card: `pa lib beta_prefix_extend`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

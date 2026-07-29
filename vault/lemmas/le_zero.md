---
title: "Lemma: le_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_zero`

Only zero is less than or equal to zero.

## Closed Peano statement

```text
forall n. n <= 0 -> n = 0
```

## Dependencies

- [[add_eq_zero_right]]

## Checked dependents

- [[gcd_exists_up_to]]
- [[gcd_balanced_bezout_exists_up_to]]
- [[factor_search_up_to]]
- [[prime_divisor_exists_up_to]]
- [[bounded_beta_crt_prefix_invariant]]
- [[sorted_empty]]
- [[sorted_singleton]]
- [[greatest_prime_divisor_search]]
- [[prime_factorization_exists_up_to]]
- [[beta_sorted_factor_le_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29 nodes**, depth **13**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib le_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

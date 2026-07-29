---
title: "Lemma: le_eq_or_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_eq_or_lt`

A witnessed inequality is either equality or a witnessed strict inequality.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) -> a = b \/ exists k. k + S a = b
```

## Dependencies

- [[zero_or_succ]]
- [[zero_add]]
- [[add_succ_left]]

## Checked dependents

- [[remainder_bound_step]]
- [[gcd_exists_up_to]]
- [[gcd_balanced_bezout_exists_up_to]]
- [[factor_property_succ]]
- [[proper_factor_lt]]
- [[beta_accumulated_product_step]]
- [[beta_crt_prefix_congruence_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **98 nodes**, depth **19**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib le_eq_or_lt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: lt_irrefl_expanded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_irrefl_expanded`

No natural is strictly below itself, with strict order fully expanded.

## Closed Peano statement

```text
forall n. ~(exists k. k + S n = n)
```

## Dependencies

- [[add_succ_left]]
- [[no_succ_add_fixed]]

## Checked dependents

- [[beta_accumulated_product_step]]
- [[beta_exclusive_accumulated_product_step]]
- [[beta_prefix_swap_last_from_entries]]
- [[finite_last_is_top_from_prefix_surjective]]
- [[finite_bounded_injective_surjective]]
- [[beta_product_replace_balance]]
- [[beta_product_swap_last_invariant]]
- [[finite_fixed_last_prefix_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **83 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib lt_irrefl_expanded`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

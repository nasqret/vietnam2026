---
title: "Lemma: succ_le_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `succ_le_succ`

Successor preserves the witness-defined order.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) -> exists r. r + S a = S b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_value_lt_scaled_base]]
- [[new_value_lt_scaled_base]]
- [[beta_prefix_product_trace_exists]]
- [[beta_product_succ_append]]
- [[beta_factor_prefix_product_append]]
- [[sorted_succ_intro]]

## Verification record

- Independently checked from the empty context.
- Certificate: **13 nodes**, depth **10**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib succ_le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

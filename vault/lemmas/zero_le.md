---
title: "Lemma: zero_le"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `zero_le`

Zero is below every natural number.

## Closed Peano statement

```text
forall n. 0 <= n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_prefix_product_trace_exists]]
- [[beta_product_succ_append]]
- [[beta_factor_prefix_product_append]]

## Verification record

- Independently checked from the empty context.
- Certificate: **7 nodes**, depth **6**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib zero_le`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

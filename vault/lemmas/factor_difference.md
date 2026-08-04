---
title: "Lemma: factor_difference"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factor_difference`

A common-factor difference is itself a multiple of that factor.

## Closed Peano statement

```text
forall c u v r. c * u = c * v + r -> exists w. r = c * w
```

## Dependencies

- [[zero_add]]
- [[add_eq_zero_right]]
- [[add_right_cancel]]
- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- [[divides_remainder]]
- [[common_divisor_divides_balanced_result]]
- [[mod_eq_ordered_gap_multiple]]

## Verification record

- Independently checked from the empty context.
- Certificate: **265 nodes**, depth **26**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib factor_difference`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mul_zero_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_zero_left`

Zero annihilates multiplication on the left.

## Closed Peano statement

```text
forall n. 0 * n = 0
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_comm]]
- [[mul_eq_one_components]]
- [[prime_two]]
- [[multiple_antisymm]]
- [[multiple_decidable]]
- [[factor_search_up_to]]
- [[prime_nonzero]]
- [[factor_nonzero_left]]
- [[prime_divisor_exists_up_to]]
- [[beta_at_self_of_bound]]
- [[prime_three]]

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **8**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib mul_zero_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

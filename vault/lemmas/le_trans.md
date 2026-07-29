---
title: "Lemma: le_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_trans`

Order witnesses compose by addition, so the defined order is transitive.

## Closed Peano statement

```text
forall n m k. n <= m -> m <= k -> n <= k
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- [[lt_of_lt_of_le]]
- [[beta_moduli_coprime_of_lt_bounded_common_multiple]]
- [[bounded_beta_crt_prefix_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **57 nodes**, depth **15**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

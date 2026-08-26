---
title: "Lemma: add_permute_outer"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_permute_outer`

Permute the outer entries of two additive pairs.

## Closed Peano statement

```text
forall a b c d. (a + b) + (c + d) = (c + b) + (a + d)
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- [[balanced_bezout_euclid_step]]
- [[mod_eq_add]]

## Verification record

- Independently checked from the empty context.
- Certificate: **149 nodes**, depth **15**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib add_permute_outer`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

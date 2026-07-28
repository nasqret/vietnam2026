---
title: "Lemma: antisymm_from_witnesses"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `antisymm_from_witnesses`

Opposing additive witnesses force equality.

## Closed Peano statement

```text
forall a b n m. a + n = m -> b + m = n -> n = m
```

## Dependencies

- [[add_assoc]]
- [[drop_add_prefix_from_fixed]]

## Checked dependents

- [[le_antisymm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **135 nodes**, depth **29**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib antisymm_from_witnesses`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

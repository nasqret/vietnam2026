---
title: "Lemma: le_antisymm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_antisymm`

The witness-defined order is antisymmetric.

## Closed Peano statement

```text
forall n m. n <= m -> m <= n -> n = m
```

## Dependencies

- [[antisymm_from_witnesses]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **137 nodes**, depth **29**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_antisymm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

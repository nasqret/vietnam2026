---
title: "Lemma: mul_le_mul_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_le_mul_right`

Right multiplication preserves the witness-defined order.

## Closed Peano statement

```text
forall a b c. (exists k. k + a = b) -> exists r. r + a * c = b * c
```

## Dependencies

- [[add_mul]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **343 nodes**, depth **26**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib mul_le_mul_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

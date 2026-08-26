---
title: "Lemma: mul_le_mul_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_le_mul_left`

Left multiplication preserves the witness-defined order.

## Closed Peano statement

```text
forall a b c. (exists k. k + a = b) -> exists r. r + c * a = c * b
```

## Dependencies

- [[mul_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **94 nodes**, depth **17**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib mul_le_mul_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

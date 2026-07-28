---
title: "Lemma: mul_lt_mul_succ_left_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_lt_mul_succ_left_nonzero`

Multiplication by a nonzero left factor strictly increases across a successor step.

## Closed Peano statement

```text
forall c a. ~(c = 0) -> exists r. r + S (c * a) = c * S a
```

## Dependencies

- [[add_comm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **94 nodes**, depth **26**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib mul_lt_mul_succ_left_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

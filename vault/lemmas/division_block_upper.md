---
title: "Lemma: division_block_upper"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `division_block_upper`

A bounded remainder keeps its decomposition below the next divisor block.

## Closed Peano statement

```text
forall d q r. (exists k. k + S r = d) -> exists k. k + S (d * q + r) = d * S q
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **159 nodes**, depth **19**.
- Authored script length: **34 commands**.
- Runtime card: `pa lib division_block_upper`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

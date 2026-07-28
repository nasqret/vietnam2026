---
title: "Lemma: zero_remainder_implies_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `zero_remainder_implies_multiple`

A quotient decomposition with zero remainder supplies a divisibility witness.

## Closed Peano statement

```text
forall m n q. n = m * q + 0 -> exists k. n = m * k
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **13 nodes**, depth **10**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib zero_remainder_implies_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

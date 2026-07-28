---
title: "Lemma: factor_nonzero_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factor_nonzero_left`

The left factor of a nonzero product is nonzero.

## Closed Peano statement

```text
forall n c d. ~(n = 0) -> n = c * d -> ~(c = 0)
```

## Dependencies

- [[mul_zero_left]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **37 nodes**, depth **12**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib factor_nonzero_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

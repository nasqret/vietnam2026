---
title: "Lemma: remainder_unique_same_quotient"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `remainder_unique_same_quotient`

Equal decompositions with the same quotient have equal remainders.

## Closed Peano statement

```text
forall d q r s. d * q + r = d * q + s -> r = s
```

## Dependencies

- [[add_left_cancel]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **171 nodes**, depth **25**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib remainder_unique_same_quotient`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

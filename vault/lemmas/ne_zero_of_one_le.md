---
title: "Lemma: ne_zero_of_one_le"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `ne_zero_of_one_le`

A natural at least one is nonzero.

## Closed Peano statement

```text
forall n. 1 <= n -> ~(n = 0)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **12**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib ne_zero_of_one_le`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

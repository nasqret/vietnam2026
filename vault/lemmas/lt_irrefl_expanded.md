---
title: "Lemma: lt_irrefl_expanded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_irrefl_expanded`

No natural is strictly below itself, with strict order fully expanded.

## Closed Peano statement

```text
forall n. ~(exists k. k + S n = n)
```

## Dependencies

- [[add_succ_left]]
- [[no_succ_add_fixed]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **63 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib lt_irrefl_expanded`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: nonzero_is_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `nonzero_is_succ`

Every nonzero natural has a predecessor.

## Closed Peano statement

```text
forall n. ~(n = 0) -> exists k. n = S k
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **11 nodes**, depth **6**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib nonzero_is_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: lt_of_lt_of_le"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_of_lt_of_le`

Strict order followed by weak order remains strict.

## Closed Peano statement

```text
forall a b c. (exists k. k + S a = b) -> (exists k. k + b = c) -> exists k. k + S a = c
```

## Dependencies

- [[le_trans]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **51 nodes**, depth **21**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib lt_of_lt_of_le`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

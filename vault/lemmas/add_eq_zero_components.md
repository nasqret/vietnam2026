---
title: "Lemma: add_eq_zero_components"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_eq_zero_components`

Both summands of a zero sum are zero.

## Closed Peano statement

```text
forall a b. a + b = 0 -> a = 0 /\ b = 0
```

## Dependencies

- [[add_eq_zero_left]]
- [[add_eq_zero_right]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **147 nodes**, depth **15**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib add_eq_zero_components`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: le_add_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_add_left`

Adding on the left produces an explicit order witness.

## Closed Peano statement

```text
forall a b. exists k. k + a = b + a
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4 nodes**, depth **4**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib le_add_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

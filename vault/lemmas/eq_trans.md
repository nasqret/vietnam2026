---
title: "Lemma: eq_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `eq_trans`

Equality is transitive.

## Closed Peano statement

```text
forall a b c. a = b -> b = c -> a = c
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **8 nodes**, depth **7**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib eq_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

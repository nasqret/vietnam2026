---
title: "Lemma: le_or_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_or_lt`

Any two naturals satisfy weak order in one direction or strict order in the other.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) \/ exists k. k + S b = a
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **48 nodes**, depth **17**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib le_or_lt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

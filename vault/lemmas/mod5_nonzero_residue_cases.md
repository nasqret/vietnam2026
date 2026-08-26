---
title: "Lemma: mod5_nonzero_residue_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_nonzero_residue_cases`

A nonmultiple of five lies in one of the four nonzero residue classes.

## Closed Peano statement

```text
forall n. ~(exists q. n = 5 * q) -> exists q. n = 5 * q + 1 \/ n = 5 * q + 2 \/ n = 5 * q + 3 \/ n = 5 * q + 4
```

## Dependencies

- [[mod5_residue_complete]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **287 nodes**, depth **29**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib mod5_nonzero_residue_cases`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

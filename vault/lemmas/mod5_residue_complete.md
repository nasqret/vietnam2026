---
title: "Lemma: mod5_residue_complete"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_residue_complete`

Every natural number has one of the five canonical residues modulo five.

## Closed Peano statement

```text
forall n. exists q. n = 5 * q \/ n = 5 * q + 1 \/ n = 5 * q + 2 \/ n = 5 * q + 3 \/ n = 5 * q + 4
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mod5_nonzero_residue_cases]]
- [[mod5_fourth_power_one]]

## Verification record

- Independently checked from the empty context.
- Certificate: **248 nodes**, depth **28**.
- Authored script length: **41 commands**.
- Runtime card: `pa lib mod5_residue_complete`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

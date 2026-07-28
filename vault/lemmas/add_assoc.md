---
title: "Lemma: add_assoc"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_assoc`

Addition is associative.

## Closed Peano statement

```text
forall n m k. (n + m) + k = n + (m + k)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_succ_left]]
- [[mul_add]]
- [[le_trans]]
- [[antisymm_from_witnesses]]
- [[add_residue]]
- [[add_residue_lift]]
- [[square_decomp]]

## Verification record

- Independently checked from the empty context.
- Certificate: **33 nodes**, depth **12**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib add_assoc`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: no_succ_add_fixed"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `no_succ_add_fixed`

Adding a positive successor cannot leave a natural number fixed.

## Closed Peano statement

```text
forall p n. S p + n = n -> false
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[drop_add_prefix_from_fixed]]
- [[lt_irrefl_expanded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **30 nodes**, depth **12**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib no_succ_add_fixed`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

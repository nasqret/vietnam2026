---
title: "Lemma: lt_trichotomy"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_trichotomy`

Two naturals are equal or strictly ordered in exactly one displayed direction.

## Closed Peano statement

```text
forall a b. a = b \/ ((exists k. k + S a = b) \/ exists k. k + S b = a)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **66 nodes**, depth **19**.
- Authored script length: **39 commands**.
- Runtime card: `pa lib lt_trichotomy`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: odd_half_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_half_exists_unique`

Every odd natural has a unique half witness.

## Closed Peano statement

```text
forall n. (exists a. n = 2 * a + 1) -> exists h. n = 2 * h + 1 /\ forall k. n = 2 * k + 1 -> h = k
```

## Dependencies

- [[odd_half_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **319 nodes**, depth **26**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib odd_half_exists_unique`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

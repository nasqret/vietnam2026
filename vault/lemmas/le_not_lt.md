---
title: "Lemma: le_not_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_not_lt`

A weak inequality excludes strict inequality in the reverse direction.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) -> ~ (exists k. k + S b = a)
```

## Dependencies

- [[lt_not_le]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **74 nodes**, depth **24**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_not_lt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

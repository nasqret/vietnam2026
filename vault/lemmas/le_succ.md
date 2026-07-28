---
title: "Lemma: le_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_succ`

A weak inequality remains true after raising its upper bound by one.

## Closed Peano statement

```text
forall a b. (exists k. k + a = b) -> exists r. r + a = S b
```

## Dependencies

- [[add_succ_left]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **36 nodes**, depth **16**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

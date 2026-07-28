---
title: "Lemma: lt_to_le"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_to_le`

A witnessed strict inequality entails the corresponding weak inequality.

## Closed Peano statement

```text
forall a b. (exists k. k + S a = b) -> exists r. r + a = b
```

## Dependencies

- [[add_succ_left]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **44 nodes**, depth **12**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib lt_to_le`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

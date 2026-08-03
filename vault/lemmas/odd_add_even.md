---
title: "Lemma: odd_add_even"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_add_even`

An odd natural plus an even natural is odd.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a + 1) -> (exists b. n = 2 * b) -> exists c. m + n = 2 * c + 1
```

## Dependencies

- [[mul_add]]
- [[add_succ_left]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **151 nodes**, depth **21**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib odd_add_even`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

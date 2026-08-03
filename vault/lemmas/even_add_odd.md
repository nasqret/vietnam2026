---
title: "Lemma: even_add_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `even_add_odd`

An even natural plus an odd natural is odd.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a) -> (exists b. n = 2 * b + 1) -> exists c. m + n = 2 * c + 1
```

## Dependencies

- [[mul_add]]
- [[add_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **157 nodes**, depth **22**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib even_add_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

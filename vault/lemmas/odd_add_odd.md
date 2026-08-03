---
title: "Lemma: odd_add_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_add_odd`

The sum of two odd naturals is even.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a + 1) -> (exists b. n = 2 * b + 1) -> exists c. m + n = 2 * c
```

## Dependencies

- [[mul_add]]
- [[add_succ_left]]
- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **302 nodes**, depth **32**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib odd_add_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

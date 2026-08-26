---
title: "Lemma: odd_mul_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_mul_odd`

The product of two odd naturals is odd.

## Closed Peano statement

```text
forall m n. (exists a. m = 2 * a + 1) -> (exists b. n = 2 * b + 1) -> exists c. m * n = 2 * c + 1
```

## Dependencies

- [[mul_add]]
- [[add_mul]]
- [[add_assoc]]
- [[add_succ_left]]
- [[mul_double_right]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **897 nodes**, depth **31**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib odd_mul_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

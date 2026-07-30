---
title: "Lemma: mod4_one_is_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod4_one_is_odd`

A natural congruent to one modulo four is odd.

## Closed Peano statement

```text
forall n. (exists a. n = 4 * a + 1) -> exists h. n = 2 * h + 1
```

## Dependencies

- [[four_mul_eq_double_double]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **191 nodes**, depth **20**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib mod4_one_is_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

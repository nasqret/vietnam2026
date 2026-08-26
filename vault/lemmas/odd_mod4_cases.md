---
title: "Lemma: odd_mod4_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_mod4_cases`

Every odd natural is congruent to one or three modulo four.

## Closed Peano statement

```text
forall n. (exists h. n = 2 * h + 1) -> (exists a. n = 4 * a + 1) \/ exists b. n = 4 * b + 3
```

## Dependencies

- [[parity_cases]]
- [[mul_add]]
- [[four_mul_eq_double_double]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **450 nodes**, depth **32**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib odd_mod4_cases`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: odd_half_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `odd_half_unique`

The half witness in an odd decomposition is unique.

## Closed Peano statement

```text
forall n a b. n = 2 * a + 1 -> n = 2 * b + 1 -> a = b
```

## Dependencies

- [[add_right_cancel]]
- [[mul_left_cancel_nonzero]]

## Checked dependents

- [[odd_half_exists_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **292 nodes**, depth **25**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib odd_half_unique`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

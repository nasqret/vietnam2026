---
title: "Lemma: successor_odd_of_even"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `successor_odd_of_even`

The successor of an even natural is odd.

## Closed Peano statement

```text
forall n. (exists a. n = 2 * a) -> exists b. S n = 2 * b + 1
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[even_successor_to_odd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **18 nodes**, depth **10**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib successor_odd_of_even`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

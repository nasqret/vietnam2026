---
title: "Lemma: successor_even_of_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `successor_even_of_odd`

The successor of an odd natural is even.

## Closed Peano statement

```text
forall n. (exists a. n = 2 * a + 1) -> exists b. S n = 2 * b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[odd_successor_to_even]]

## Verification record

- Independently checked from the empty context.
- Certificate: **46 nodes**, depth **16**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib successor_even_of_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

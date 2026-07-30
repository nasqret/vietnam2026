---
title: "Lemma: parity_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `parity_cases`

Every natural has a constructive even-or-odd witness.

## Closed Peano statement

```text
forall n. exists k. n = 2 * k \/ n = 2 * k + 1
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[odd_mod4_cases]]
- [[prime_ne_two_is_odd]]
- [[even_successor_to_odd]]
- [[odd_successor_to_even]]

## Verification record

- Independently checked from the empty context.
- Certificate: **80 nodes**, depth **19**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib parity_cases`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

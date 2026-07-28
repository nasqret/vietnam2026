---
title: "Lemma: one_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `one_multiple`

Every natural number is a multiple of one.

## Closed Peano statement

```text
forall n. exists q. n = 1 * q
```

## Dependencies

- [[one_mul]]

## Checked dependents

- [[coprime_to_is_gcd_one]]

## Verification record

- Independently checked from the empty context.
- Certificate: **30 nodes**, depth **13**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib one_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

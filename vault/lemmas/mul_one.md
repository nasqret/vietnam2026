---
title: "Lemma: mul_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_one`

One is a right identity for multiplication.

## Closed Peano statement

```text
forall n. n * 1 = n
```

## Dependencies

- [[zero_add]]

## Checked dependents

- [[multiple_refl]]

## Verification record

- Independently checked from the empty context.
- Certificate: **31 nodes**, depth **14**.
- Authored script length: **2 commands**.
- Runtime card: `pa lib mul_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

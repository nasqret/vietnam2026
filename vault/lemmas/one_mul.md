---
title: "Lemma: one_mul"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `one_mul`

One is a left identity for multiplication.

## Closed Peano statement

```text
forall n. 1 * n = n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[mul_eq_one_components]]
- [[one_multiple]]
- [[coprime_to_is_gcd_one]]

## Verification record

- Independently checked from the empty context.
- Certificate: **26 nodes**, depth **9**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib one_mul`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

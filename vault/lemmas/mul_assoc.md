---
title: "Lemma: mul_assoc"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_assoc`

Multiplication is associative.

## Closed Peano statement

```text
forall n m k. (n * m) * k = n * (m * k)
```

## Dependencies

- [[mul_add]]

## Checked dependents

- [[multiple_mul_right]]
- [[multiple_trans]]
- [[square_decomp]]

## Verification record

- Independently checked from the empty context.
- Certificate: **104 nodes**, depth **31**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib mul_assoc`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

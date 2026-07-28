---
title: "Lemma: divisor_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `divisor_one`

Every natural divisor of one equals one.

## Closed Peano statement

```text
forall d. (exists y. 1 = d * y) -> d = 1
```

## Dependencies

- [[mul_eq_one_components]]

## Checked dependents

- [[coprime_one_right]]
- [[coprime_one_left]]
- [[is_gcd_one_to_coprime]]

## Verification record

- Independently checked from the empty context.
- Certificate: **188 nodes**, depth **28**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib divisor_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: multiple_refl"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_refl`

Every natural number is a multiple of itself.

## Closed Peano statement

```text
forall a. exists q. a = a * q
```

## Dependencies

- [[mul_one]]

## Checked dependents

- [[is_gcd_of_dvd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **33 nodes**, depth **16**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib multiple_refl`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

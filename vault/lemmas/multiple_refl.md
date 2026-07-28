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

- [[is_gcd_zero_right]]
- [[is_gcd_of_dvd]]
- [[gcd_exists_up_to]]
- [[gauss_coprime_cancel]]

## Verification record

- Independently checked from the empty context.
- Certificate: **39 nodes**, depth **10**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib multiple_refl`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

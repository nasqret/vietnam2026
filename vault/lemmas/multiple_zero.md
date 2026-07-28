---
title: "Lemma: multiple_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_zero`

Zero is a multiple of every natural number.

## Closed Peano statement

```text
forall a. exists q. 0 = a * q
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[is_gcd_zero_right]]

## Verification record

- Independently checked from the empty context.
- Certificate: **7 nodes**, depth **6**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib multiple_zero`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

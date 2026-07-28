---
title: "Lemma: multiple_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_trans`

The multiple relation is transitive.

## Closed Peano statement

```text
forall a b n. (exists q. n = a * q) -> (exists r. a = b * r) -> exists s. n = b * s
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- [[prime_divisor_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **137 nodes**, depth **18**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib multiple_trans`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

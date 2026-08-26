---
title: "Lemma: multiple_antisymm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_antisymm`

Mutual divisibility is antisymmetric over natural numbers.

## Closed Peano statement

```text
forall a b. (exists x. b = a * x) -> (exists y. a = b * y) -> a = b
```

## Dependencies

- [[zero_or_succ]]
- [[mul_zero_left]]
- [[mul_assoc]]
- [[mul_one]]
- [[mul_left_cancel_nonzero]]
- [[mul_eq_one_components]]

## Checked dependents

- [[is_gcd_unique]]
- [[is_lcm_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **646 nodes**, depth **33**.
- Authored script length: **50 commands**.
- Runtime card: `pa lib multiple_antisymm`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

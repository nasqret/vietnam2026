---
title: "Lemma: mod_eq_mul_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_mul_right`

Balanced congruence is preserved by multiplication on the right.

## Closed Peano statement

```text
forall m a b c. (exists u v. a + m * u = b + m * v) -> exists r s. (a * c) + m * r = (b * c) + m * s
```

## Dependencies

- [[add_mul]]
- [[mul_assoc]]

## Checked dependents

- [[mod_eq_mul_left]]
- [[mod_eq_mul]]
- [[mod_eq_cancel_coprime]]
- [[bounded_mod_inverse_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **484 nodes**, depth **26**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib mod_eq_mul_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

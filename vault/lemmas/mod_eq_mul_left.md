---
title: "Lemma: mod_eq_mul_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_mul_left`

Balanced congruence is preserved by multiplication on the left.

## Closed Peano statement

```text
forall m a b c. (exists u v. a + m * u = b + m * v) -> exists r s. (c * a) + m * r = (c * b) + m * s
```

## Dependencies

- [[mod_eq_mul_right]]
- [[mul_comm]]

## Checked dependents

- [[mod_eq_mul]]
- [[binary_crt]]
- [[mod_eq_cancel_coprime]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **738 nodes**, depth **27**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib mod_eq_mul_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

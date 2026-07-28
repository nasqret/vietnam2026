---
title: "Lemma: mod_eq_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_trans`

Balanced natural congruence is transitive.

## Closed Peano statement

```text
forall m a b c. (exists u v. a + m * u = b + m * v) -> (exists r s. b + m * r = c + m * s) -> exists x y. a + m * x = c + m * y
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]
- [[mul_add]]

## Checked dependents

- [[mod_eq_mul]]
- [[mod_eq_to_remainder_decomposition]]
- [[binary_crt]]
- [[binary_crt_fold_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **252 nodes**, depth **29**.
- Authored script length: **42 commands**.
- Runtime card: `pa lib mod_eq_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

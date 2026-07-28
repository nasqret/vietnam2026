---
title: "Lemma: mod_eq_add"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_add`

Balanced natural congruence respects addition.

## Closed Peano statement

```text
forall m a b c d. (exists u v. a + m * u = b + m * v) -> (exists r s. c + m * r = d + m * s) -> exists x y. (a + c) + m * x = (b + d) + m * y
```

## Dependencies

- [[mul_add]]
- [[add_comm]]
- [[add_permute_outer]]

## Checked dependents

- [[binary_crt]]

## Verification record

- Independently checked from the empty context.
- Certificate: **370 nodes**, depth **30**.
- Authored script length: **42 commands**.
- Runtime card: `pa lib mod_eq_add`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

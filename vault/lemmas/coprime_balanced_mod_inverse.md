---
title: "Lemma: coprime_balanced_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_balanced_mod_inverse`

Balanced Bezout coefficients give a subtraction-free modular inverse.

## Closed Peano statement

```text
forall a m. (forall d. (exists x. a = d * x) -> (exists y. m = d * y) -> d = 1) -> exists xp xn u v. a * xp + m * u = (1 + a * xn) + m * v
```

## Dependencies

- [[coprime_balanced_bezout]]
- [[add_assoc]]

## Checked dependents

- [[coprime_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2365 nodes**, depth **49**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib coprime_balanced_mod_inverse`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

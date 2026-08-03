---
title: "Lemma: coprime_symm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_symm`

Coprimality in its expanded common-divisor form is symmetric.

## Closed Peano statement

```text
forall a b. (forall d. (exists x. a = d * x) -> (exists y. b = d * y) -> d = 1) -> forall c. (exists u. b = c * u) -> (exists v. a = c * v) -> c = 1
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[coprime_mul_right]]
- [[prime_mod_cancel]]

## Verification record

- Independently checked from the empty context.
- Certificate: **15 nodes**, depth **11**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib coprime_symm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

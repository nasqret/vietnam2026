---
title: "Lemma: coprime_balanced_bezout"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_balanced_bezout`

Coprime inputs admit balanced natural Bezout coefficients with result one.

## Closed Peano statement

```text
forall a b. (forall d. (exists x. a = d * x) -> (exists y. b = d * y) -> d = 1) -> exists xp yp xn yn. a * xp + b * yp = 1 + (a * xn + b * yn)
```

## Dependencies

- [[gcd_balanced_bezout_exists]]

## Checked dependents

- [[gauss_coprime_cancel]]
- [[binary_crt]]
- [[coprime_balanced_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2304 nodes**, depth **48**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib coprime_balanced_bezout`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

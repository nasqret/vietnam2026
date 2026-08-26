---
title: "Lemma: bezout_mod_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bezout_mod_right`

A balanced Bezout identity selects the left coefficient modulo the right modulus.

## Closed Peano statement

```text
forall m n xp yp xn yn. m * xp + n * yp = 1 + (m * xn + n * yn) -> exists u v. m * xp + n * u = (1 + m * xn) + n * v
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- [[binary_crt]]

## Verification record

- Independently checked from the empty context.
- Certificate: **50 nodes**, depth **16**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib bezout_mod_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: bezout_mod_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bezout_mod_left`

A balanced Bezout identity selects the right coefficient modulo the left modulus.

## Closed Peano statement

```text
forall m n xp yp xn yn. m * xp + n * yp = 1 + (m * xn + n * yn) -> exists u v. n * yp + m * u = (1 + n * yn) + m * v
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- [[binary_crt]]

## Verification record

- Independently checked from the empty context.
- Certificate: **134 nodes**, depth **19**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib bezout_mod_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

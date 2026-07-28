---
title: "Lemma: dvd_to_mod_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `dvd_to_mod_zero`

A multiple is balanced-congruent to zero.

## Closed Peano statement

```text
forall m a. (exists k. a = m * k) -> exists u v. a + m * u = 0 + m * v
```

## Dependencies

- [[zero_add]]

## Checked dependents

- [[binary_crt]]

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **14**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib dvd_to_mod_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_predecessor_cancel"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_predecessor_cancel`

The predecessor of a successor acts as minus one in balanced congruence.

## Closed Peano statement

```text
forall k a z. exists u v. ((a + z) + k * z) + S k * u = a + S k * v
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]
- [[mul_succ_left]]

## Checked dependents

- [[binary_crt]]
- [[coprime_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **315 nodes**, depth **25**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib mod_eq_predecessor_cancel`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

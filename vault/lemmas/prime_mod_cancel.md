---
title: "Lemma: prime_mod_cancel"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_mod_cancel`

A nonzero residue factor cancels from congruence modulo a prime.

## Closed Peano statement

```text
forall p a x y. (~(p = 1) /\ forall c e. p = c * e -> c = 1 \/ e = 1) -> ~(exists k. a = p * k) -> (exists u v. (a * x) + p * u = (a * y) + p * v) -> exists r s. x + p * r = y + p * s
```

## Dependencies

- [[prime_nonzero]]
- [[prime_not_divides_coprime]]
- [[coprime_symm]]
- [[mod_eq_cancel_coprime]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **7494 nodes**, depth **56**.
- Authored script length: **32 commands**.
- Runtime card: `pa lib prime_mod_cancel`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

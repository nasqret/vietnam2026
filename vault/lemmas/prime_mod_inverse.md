---
title: "Lemma: prime_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_mod_inverse`

A nonzero residue modulo a prime has a natural modular inverse.

## Closed Peano statement

```text
forall p a. (~(p = 1) /\ forall c e. p = c * e -> c = 1 \/ e = 1) -> ~(exists k. a = p * k) -> exists z u v. a * z + p * u = 1 + p * v
```

## Dependencies

- [[prime_nonzero]]
- [[prime_not_divides_coprime]]
- [[coprime_mod_inverse]]

## Checked dependents

- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5491 nodes**, depth **54**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib prime_mod_inverse`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

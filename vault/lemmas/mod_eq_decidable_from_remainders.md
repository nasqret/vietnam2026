---
title: "Lemma: mod_eq_decidable_from_remainders"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_decidable_from_remainders`

Canonical bounded remainders constructively decide congruence.

## Closed Peano statement

```text
forall p a b qa ra qb rb. a = qa * p + ra -> (exists ha. ha + S ra = p) -> b = qb * p + rb -> (exists hb. hb + S rb = p) -> (exists u v. a + p * u = b + p * v) \/ ~(exists u v. a + p * u = b + p * v)
```

## Dependencies

- [[eq_decidable]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[mod_eq_decidable_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1693 nodes**, depth **64**.
- Authored script length: **89 commands**.
- Runtime card: `pa lib mod_eq_decidable_from_remainders`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

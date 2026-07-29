---
title: "Lemma: beta_at_to_mod_eq"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_to_mod_eq`

Every expanded Gödel-beta value is balanced-congruent to its code.

## Closed Peano statement

```text
forall b c i x. ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x) -> exists u v. b + S ((S i) * c) * u = x + S ((S i) * c) * v
```

## Dependencies

- [[remainder_decomposition_to_mod_eq]]

## Checked dependents

- [[bounded_beta_crt_prefix_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **358 nodes**, depth **27**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib beta_at_to_mod_eq`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: predecessor_square_mod_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `predecessor_square_mod_one`

The predecessor of a successor squares to one modulo that successor.

## Closed Peano statement

```text
forall p r. p = S r -> exists gs_u_square gs_v_square. (r * r) + p * gs_u_square = (1) + p * gs_v_square
```

## Dependencies

- [[mul_one]]
- [[mul_succ_left]]
- [[add_assoc]]
- [[add_comm]]
- [[zero_add]]
- [[add_succ_left]]

## Checked dependents

- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **426 nodes**, depth **27**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib predecessor_square_mod_one`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

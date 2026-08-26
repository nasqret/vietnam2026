---
title: "Lemma: bounded_square_mod5_classify"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_square_mod5_classify`

A bounded square modulo 5 has exactly a canonical square residue.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 5) -> (exists sm_x_bc5. (exists sm_h_bc5. sm_h_bc5 + S sm_x_bc5 = 5) /\ exists sm_u_bc5 sm_v_bc5. sm_x_bc5 * sm_x_bc5 + 5 * sm_u_bc5 = a + 5 * sm_v_bc5) -> (a = 0 \/ a = 1 \/ a = 4)
```

## Dependencies

- [[lt_five_cases]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[qres_mod5_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2567 nodes**, depth **62**.
- Authored script length: **166 commands**.
- Runtime card: `pa lib bounded_square_mod5_classify`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

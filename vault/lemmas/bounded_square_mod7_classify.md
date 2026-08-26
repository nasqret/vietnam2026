---
title: "Lemma: bounded_square_mod7_classify"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_square_mod7_classify`

A bounded square modulo 7 has exactly a canonical square residue.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 7) -> (exists sm_x_bc7. (exists sm_h_bc7. sm_h_bc7 + S sm_x_bc7 = 7) /\ exists sm_u_bc7 sm_v_bc7. sm_x_bc7 * sm_x_bc7 + 7 * sm_u_bc7 = a + 7 * sm_v_bc7) -> (a = 0 \/ a = 1 \/ a = 2 \/ a = 4)
```

## Dependencies

- [[lt_seven_cases]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[qres_mod7_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4033 nodes**, depth **91**.
- Authored script length: **233 commands**.
- Runtime card: `pa lib bounded_square_mod7_classify`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

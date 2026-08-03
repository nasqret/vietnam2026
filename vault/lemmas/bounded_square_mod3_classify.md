---
title: "Lemma: bounded_square_mod3_classify"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_square_mod3_classify`

A bounded square modulo 3 has exactly a canonical square residue.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 3) -> (exists sm_x_bc3. (exists sm_h_bc3. sm_h_bc3 + S sm_x_bc3 = 3) /\ exists sm_u_bc3 sm_v_bc3. sm_x_bc3 * sm_x_bc3 + 3 * sm_u_bc3 = a + 3 * sm_v_bc3) -> (a = 0 \/ a = 1)
```

## Dependencies

- [[lt_three_cases]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[qres_mod3_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1767 nodes**, depth **62**.
- Authored script length: **101 commands**.
- Runtime card: `pa lib bounded_square_mod3_classify`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

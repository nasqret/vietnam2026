---
title: "Lemma: quadratic_residue_bounded_equiv"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `quadratic_residue_bounded_equiv`

Every square witness has an equivalent canonical bounded root.

## Closed Peano statement

```text
forall p a. ~(p = 0) -> (((exists qr_x_unbounded. exists qr_u_unbounded qr_v_unbounded. qr_x_unbounded * qr_x_unbounded + p * qr_u_unbounded = a + p * qr_v_unbounded) -> (exists qr_x_bounded. (exists qr_h_bounded. qr_h_bounded + S qr_x_bounded = p) /\ exists qr_u_bounded qr_v_bounded. qr_x_bounded * qr_x_bounded + p * qr_u_bounded = a + p * qr_v_bounded)) /\ ((exists qr_x_bounded. (exists qr_h_bounded. qr_h_bounded + S qr_x_bounded = p) /\ exists qr_u_bounded qr_v_bounded. qr_x_bounded * qr_x_bounded + p * qr_u_bounded = a + p * qr_v_bounded) -> (exists qr_x_unbounded. exists qr_u_unbounded qr_v_unbounded. qr_x_unbounded * qr_x_unbounded + p * qr_u_unbounded = a + p * qr_v_unbounded)))
```

## Dependencies

- [[division_remainder_exists]]
- [[square_residue_witness]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mul_comm]]
- [[zero_add]]

## Checked dependents

- [[quadratic_residue_decidable_nonzero]]
- [[qres_mod3_canonical_iff]]
- [[qres_mod5_canonical_iff]]
- [[qres_mod7_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2151 nodes**, depth **34**.
- Authored script length: **64 commands**.
- Runtime card: `pa lib quadratic_residue_bounded_equiv`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

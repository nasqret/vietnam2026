---
title: "Lemma: quadratic_residue_bounded_decidable_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `quadratic_residue_bounded_decidable_nonzero`

A nonzero modulus admits a finite constructive residue search.

## Closed Peano statement

```text
forall p a. ~(p = 0) -> (exists qr_x_bounded. (exists qr_h_bounded. qr_h_bounded + S qr_x_bounded = p) /\ exists qr_u_bounded qr_v_bounded. qr_x_bounded * qr_x_bounded + p * qr_u_bounded = a + p * qr_v_bounded) \/ ~(exists qr_x_bounded. (exists qr_h_bounded. qr_h_bounded + S qr_x_bounded = p) /\ exists qr_u_bounded qr_v_bounded. qr_x_bounded * qr_x_bounded + p * qr_u_bounded = a + p * qr_v_bounded)
```

## Dependencies

- [[nonzero_is_succ]]
- [[quadratic_residue_search_up_to]]

## Checked dependents

- [[quadratic_residue_decidable_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2554 nodes**, depth **70**.
- Authored script length: **46 commands**.
- Runtime card: `pa lib quadratic_residue_bounded_decidable_nonzero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

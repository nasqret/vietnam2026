---
title: "Lemma: qres_mod7_canonical_iff"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod7_canonical_iff`

For canonical values, the displayed list is exactly QRes modulo 7.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 7) -> (((exists sm_x_iffq7. exists sm_u_iffq7 sm_v_iffq7. sm_x_iffq7 * sm_x_iffq7 + 7 * sm_u_iffq7 = a + 7 * sm_v_iffq7) -> (a = 0 \/ a = 1 \/ a = 2 \/ a = 4)) /\ ((a = 0 \/ a = 1 \/ a = 2 \/ a = 4) -> (exists sm_x_iffq7. exists sm_u_iffq7 sm_v_iffq7. sm_x_iffq7 * sm_x_iffq7 + 7 * sm_u_iffq7 = a + 7 * sm_v_iffq7)))
```

## Dependencies

- [[quadratic_residue_bounded_equiv]]
- [[succ_ne_zero]]
- [[bounded_square_mod7_classify]]
- [[qres_mod7_zero]]
- [[qres_mod7_one]]
- [[qres_mod7_two]]
- [[qres_mod7_four]]

## Checked dependents

- [[not_qres_mod7_three]]
- [[not_qres_mod7_five]]
- [[not_qres_mod7_six]]

## Verification record

- Independently checked from the empty context.
- Certificate: **6648 nodes**, depth **94**.
- Authored script length: **30 commands**.
- Runtime card: `pa lib qres_mod7_canonical_iff`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

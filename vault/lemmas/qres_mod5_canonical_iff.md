---
title: "Lemma: qres_mod5_canonical_iff"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod5_canonical_iff`

For canonical values, the displayed list is exactly QRes modulo 5.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 5) -> (((exists sm_x_iffq5. exists sm_u_iffq5 sm_v_iffq5. sm_x_iffq5 * sm_x_iffq5 + 5 * sm_u_iffq5 = a + 5 * sm_v_iffq5) -> (a = 0 \/ a = 1 \/ a = 4)) /\ ((a = 0 \/ a = 1 \/ a = 4) -> (exists sm_x_iffq5. exists sm_u_iffq5 sm_v_iffq5. sm_x_iffq5 * sm_x_iffq5 + 5 * sm_u_iffq5 = a + 5 * sm_v_iffq5)))
```

## Dependencies

- [[quadratic_residue_bounded_equiv]]
- [[succ_ne_zero]]
- [[bounded_square_mod5_classify]]
- [[qres_mod5_zero]]
- [[qres_mod5_one]]
- [[qres_mod5_four]]

## Checked dependents

- [[not_qres_mod5_two]]
- [[not_qres_mod5_three]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4955 nodes**, depth **65**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib qres_mod5_canonical_iff`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

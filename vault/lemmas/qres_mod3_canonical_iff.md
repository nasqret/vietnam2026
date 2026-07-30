---
title: "Lemma: qres_mod3_canonical_iff"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod3_canonical_iff`

For canonical values, the displayed list is exactly QRes modulo 3.

## Closed Peano statement

```text
forall a. (exists h. h + S a = 3) -> (((exists sm_x_iffq3. exists sm_u_iffq3 sm_v_iffq3. sm_x_iffq3 * sm_x_iffq3 + 3 * sm_u_iffq3 = a + 3 * sm_v_iffq3) -> (a = 0 \/ a = 1)) /\ ((a = 0 \/ a = 1) -> (exists sm_x_iffq3. exists sm_u_iffq3 sm_v_iffq3. sm_x_iffq3 * sm_x_iffq3 + 3 * sm_u_iffq3 = a + 3 * sm_v_iffq3)))
```

## Dependencies

- [[quadratic_residue_bounded_equiv]]
- [[succ_ne_zero]]
- [[bounded_square_mod3_classify]]
- [[qres_mod3_zero]]
- [[qres_mod3_one]]

## Checked dependents

- [[not_qres_mod3_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4050 nodes**, depth **65**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib qres_mod3_canonical_iff`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

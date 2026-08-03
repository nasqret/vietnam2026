---
title: "Lemma: not_qres_mod7_five"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_qres_mod7_five`

The canonical value 5 is not a quadratic residue modulo 7.

## Closed Peano statement

```text
~(exists sm_x_n7_5. exists sm_u_n7_5 sm_v_n7_5. sm_x_n7_5 * sm_x_n7_5 + 7 * sm_u_n7_5 = 5 + 7 * sm_v_n7_5)
```

## Dependencies

- [[qres_mod7_canonical_iff]]
- [[succ_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6756 nodes**, depth **95**.
- Authored script length: **58 commands**.
- Runtime card: `pa lib not_qres_mod7_five`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

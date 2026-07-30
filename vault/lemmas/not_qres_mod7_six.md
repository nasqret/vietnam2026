---
title: "Lemma: not_qres_mod7_six"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_qres_mod7_six`

The canonical value 6 is not a quadratic residue modulo 7.

## Closed Peano statement

```text
~(exists sm_x_n7_6. exists sm_u_n7_6 sm_v_n7_6. sm_x_n7_6 * sm_x_n7_6 + 7 * sm_u_n7_6 = 6 + 7 * sm_v_n7_6)
```

## Dependencies

- [[qres_mod7_canonical_iff]]
- [[succ_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6761 nodes**, depth **95**.
- Authored script length: **58 commands**.
- Runtime card: `pa lib not_qres_mod7_six`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

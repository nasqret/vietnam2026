---
title: "Lemma: not_qres_mod3_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_qres_mod3_two`

The canonical value 2 is not a quadratic residue modulo 3.

## Closed Peano statement

```text
~(exists sm_x_n3_2. exists sm_u_n3_2 sm_v_n3_2. sm_x_n3_2 * sm_x_n3_2 + 3 * sm_u_n3_2 = 2 + 3 * sm_v_n3_2)
```

## Dependencies

- [[qres_mod3_canonical_iff]]
- [[succ_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4103 nodes**, depth **66**.
- Authored script length: **22 commands**.
- Runtime card: `pa lib not_qres_mod3_two`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

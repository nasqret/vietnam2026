---
title: "Lemma: not_qres_mod5_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_qres_mod5_two`

The canonical value 2 is not a quadratic residue modulo 5.

## Closed Peano statement

```text
~(exists sm_x_n5_2. exists sm_u_n5_2 sm_v_n5_2. sm_x_n5_2 * sm_x_n5_2 + 5 * sm_u_n5_2 = 2 + 5 * sm_v_n5_2)
```

## Dependencies

- [[qres_mod5_canonical_iff]]
- [[succ_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **5025 nodes**, depth **66**.
- Authored script length: **36 commands**.
- Runtime card: `pa lib not_qres_mod5_two`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

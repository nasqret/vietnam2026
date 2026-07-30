---
title: "Lemma: not_qres_mod5_three"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_qres_mod5_three`

The canonical value 3 is not a quadratic residue modulo 5.

## Closed Peano statement

```text
~(exists sm_x_n5_3. exists sm_u_n5_3 sm_v_n5_3. sm_x_n5_3 * sm_x_n5_3 + 5 * sm_u_n5_3 = 3 + 5 * sm_v_n5_3)
```

## Dependencies

- [[qres_mod5_canonical_iff]]
- [[succ_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **5034 nodes**, depth **66**.
- Authored script length: **41 commands**.
- Runtime card: `pa lib not_qres_mod5_three`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

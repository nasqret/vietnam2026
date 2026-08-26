---
title: "Lemma: qres_mod7_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod7_zero`

The canonical value 0 is a quadratic residue modulo 7.

## Closed Peano statement

```text
exists sm_x_p7_0. exists sm_u_p7_0 sm_v_p7_0. sm_x_p7_0 * sm_x_p7_0 + 7 * sm_u_p7_0 = 0 + 7 * sm_v_p7_0
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod7_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **48 nodes**, depth **18**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod7_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

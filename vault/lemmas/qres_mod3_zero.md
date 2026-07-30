---
title: "Lemma: qres_mod3_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod3_zero`

The canonical value 0 is a quadratic residue modulo 3.

## Closed Peano statement

```text
exists sm_x_p3_0. exists sm_u_p3_0 sm_v_p3_0. sm_x_p3_0 * sm_x_p3_0 + 3 * sm_u_p3_0 = 0 + 3 * sm_v_p3_0
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod3_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **40 nodes**, depth **14**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod3_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

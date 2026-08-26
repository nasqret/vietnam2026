---
title: "Lemma: qres_mod5_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod5_zero`

The canonical value 0 is a quadratic residue modulo 5.

## Closed Peano statement

```text
exists sm_x_p5_0. exists sm_u_p5_0 sm_v_p5_0. sm_x_p5_0 * sm_x_p5_0 + 5 * sm_u_p5_0 = 0 + 5 * sm_v_p5_0
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod5_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **44 nodes**, depth **16**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod5_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: qres_mod5_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod5_one`

The canonical value 1 is a quadratic residue modulo 5.

## Closed Peano statement

```text
exists sm_x_p5_1. exists sm_u_p5_1 sm_v_p5_1. sm_x_p5_1 * sm_x_p5_1 + 5 * sm_u_p5_1 = 1 + 5 * sm_v_p5_1
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod5_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **61 nodes**, depth **16**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod5_one`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

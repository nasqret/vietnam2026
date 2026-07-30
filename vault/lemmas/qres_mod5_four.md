---
title: "Lemma: qres_mod5_four"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod5_four`

The canonical value 4 is a quadratic residue modulo 5.

## Closed Peano statement

```text
exists sm_x_p5_4. exists sm_u_p5_4 sm_v_p5_4. sm_x_p5_4 * sm_x_p5_4 + 5 * sm_u_p5_4 = 4 + 5 * sm_v_p5_4
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod5_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **90 nodes**, depth **18**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod5_four`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: qres_mod3_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod3_one`

The canonical value 1 is a quadratic residue modulo 3.

## Closed Peano statement

```text
exists sm_x_p3_1. exists sm_u_p3_1 sm_v_p3_1. sm_x_p3_1 * sm_x_p3_1 + 3 * sm_u_p3_1 = 1 + 3 * sm_v_p3_1
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod3_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **57 nodes**, depth **14**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod3_one`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: qres_mod7_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `qres_mod7_two`

The canonical value 2 is a quadratic residue modulo 7.

## Closed Peano statement

```text
exists sm_x_p7_2. exists sm_u_p7_2 sm_v_p7_2. sm_x_p7_2 * sm_x_p7_2 + 7 * sm_u_p7_2 = 2 + 7 * sm_v_p7_2
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[qres_mod7_canonical_iff]]

## Verification record

- Independently checked from the empty context.
- Certificate: **208 nodes**, depth **27**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib qres_mod7_two`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

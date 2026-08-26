---
title: "Lemma: quadratic_residue_decidable_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `quadratic_residue_decidable_nonzero`

Quadratic residuosity is constructively decidable at nonzero modulus.

## Closed Peano statement

```text
forall p a. ~(p = 0) -> (exists qr_x_unbounded. exists qr_u_unbounded qr_v_unbounded. qr_x_unbounded * qr_x_unbounded + p * qr_u_unbounded = a + p * qr_v_unbounded) \/ ~(exists qr_x_unbounded. exists qr_u_unbounded qr_v_unbounded. qr_x_unbounded * qr_x_unbounded + p * qr_u_unbounded = a + p * qr_v_unbounded)
```

## Dependencies

- [[quadratic_residue_bounded_decidable_nonzero]]
- [[quadratic_residue_bounded_equiv]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4737 nodes**, depth **71**.
- Authored script length: **23 commands**.
- Runtime card: `pa lib quadratic_residue_decidable_nonzero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: bounded_mod_inverse_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_mod_inverse_unique`

Two bounded inverses of the same residue are equal.

## Closed Peano statement

```text
forall p x y z. (exists wip_strict_gap_unique_y_bound. wip_strict_gap_unique_y_bound + S y = p) -> (exists wip_strict_gap_unique_z_bound. wip_strict_gap_unique_z_bound + S z = p) -> (exists wip_mod_left_unique_xy wip_mod_right_unique_xy. x * y + p * wip_mod_left_unique_xy = 1 + p * wip_mod_right_unique_xy) -> (exists wip_mod_left_unique_xz wip_mod_right_unique_xz. x * z + p * wip_mod_left_unique_xz = 1 + p * wip_mod_right_unique_xz) -> y = z
```

## Dependencies

- [[mod_eq_symm]]
- [[mod_eq_mul_left]]
- [[mod_eq_mul_right]]
- [[mul_assoc]]
- [[mul_comm]]
- [[mul_one]]
- [[one_mul]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[coprime_iff_unique_bounded_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2914 nodes**, depth **68**.
- Authored script length: **62 commands**.
- Runtime card: `pa lib bounded_mod_inverse_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

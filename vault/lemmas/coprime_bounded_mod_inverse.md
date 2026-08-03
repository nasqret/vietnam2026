---
title: "Lemma: coprime_bounded_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_bounded_mod_inverse`

Every coprime residue has an inverse in the canonical interval below a nonzero modulus.

## Closed Peano statement

```text
forall a m. ~(m = 0) -> (forall hmi_divisor_assumption. (exists hmi_left_factor_assumption. a = hmi_divisor_assumption * hmi_left_factor_assumption) -> (exists hmi_right_factor_assumption. m = hmi_divisor_assumption * hmi_right_factor_assumption) -> hmi_divisor_assumption = 1) -> exists r. (exists hmi_gap_result_bound. hmi_gap_result_bound + S r = m) /\ (exists hmi_left_offset_result_inverse hmi_right_offset_result_inverse. a * r + m * hmi_left_offset_result_inverse = 1 + m * hmi_right_offset_result_inverse)
```

## Dependencies

- [[canonical_remainder_exists]]
- [[coprime_mod_inverse]]
- [[mul_comm]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_mul_left]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]

## Checked dependents

- [[coprime_iff_unique_bounded_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5675 nodes**, depth **53**.
- Authored script length: **61 commands**.
- Runtime card: `pa lib coprime_bounded_mod_inverse`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

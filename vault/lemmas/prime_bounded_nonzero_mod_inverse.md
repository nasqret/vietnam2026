---
title: "Lemma: prime_bounded_nonzero_mod_inverse"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_bounded_nonzero_mod_inverse`

A nonzero residue below a prime has a nonzero bounded inverse.

## Closed Peano statement

```text
forall p a. ((~(p = 1) /\ forall qrbu_factor_left_prime_p qrbu_factor_right_prime_p. p = qrbu_factor_left_prime_p * qrbu_factor_right_prime_p -> qrbu_factor_left_prime_p = 1 \/ qrbu_factor_right_prime_p = 1)) -> ~(a = 0) -> (exists qrbu_gap_a_lt_p. qrbu_gap_a_lt_p + S a = p) -> (exists qrbu_inverse_bounded_inverse. (~(qrbu_inverse_bounded_inverse = 0) /\ ((exists qrbu_gap_bounded_inverse_bound. qrbu_gap_bounded_inverse_bound + S qrbu_inverse_bounded_inverse = p) /\ (exists qrbu_mod_left_bounded_inverse_mod qrbu_mod_right_bounded_inverse_mod. a * qrbu_inverse_bounded_inverse + p * qrbu_mod_left_bounded_inverse_mod = 1 + p * qrbu_mod_right_bounded_inverse_mod))))
```

## Dependencies

- [[prime_is_succ_succ]]
- [[prime_nonzero]]
- [[divisor_le_nonzero]]
- [[lt_not_le]]
- [[prime_mod_inverse]]
- [[division_remainder_exists]]
- [[mul_comm]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_mul_left]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]
- [[succ_ne_zero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **8684 nodes**, depth **71**.
- Authored script length: **125 commands**.
- Runtime card: `pa lib prime_bounded_nonzero_mod_inverse`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

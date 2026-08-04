---
title: "Lemma: mod_eq_common_remainder_decomposition"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_common_remainder_decomposition`

Compatible residues share one bounded remainder modulo their gcd.

## Closed Peano statement

```text
forall g a b. ~(g = 0) -> (exists hgcrt_mod_left_common_remainder_assumption hgcrt_mod_right_common_remainder_assumption. a + g * hgcrt_mod_left_common_remainder_assumption = b + g * hgcrt_mod_right_common_remainder_assumption) -> exists A B r. ((a = g * A + r /\ b = g * B + r) /\ (exists hmi_gap_common_remainder_bound. hmi_gap_common_remainder_bound + S r = g))
```

## Dependencies

- [[division_remainder_exists]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mod_eq_to_remainder_decomposition]]
- [[mul_comm]]

## Checked dependents

- [[generalized_binary_crt_sufficient_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2894 nodes**, depth **69**.
- Authored script length: **61 commands**.
- Runtime card: `pa lib mod_eq_common_remainder_decomposition`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

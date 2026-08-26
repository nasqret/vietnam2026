---
title: "Lemma: canonical_remainders_characterize_mod_eq"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_remainders_characterize_mod_eq`

Two canonical remainders are equal exactly when their dividends are congruent modulo the shared modulus.

## Closed Peano statement

```text
forall m a b r s. (((exists hcr_quotient_left. a = m * hcr_quotient_left + r) /\ exists hcr_gap_left. hcr_gap_left + S r = m)) -> (((exists hcr_quotient_right. b = m * hcr_quotient_right + s) /\ exists hcr_gap_right. hcr_gap_right + S s = m)) -> (((exists hcc_mod_left_source hcc_mod_right_source. a + m * hcc_mod_left_source = b + m * hcc_mod_right_source) -> r = s) /\ (r = s -> (exists hcc_mod_left_result hcc_mod_right_result. a + m * hcc_mod_left_result = b + m * hcc_mod_right_result)))
```

## Dependencies

- [[mul_comm]]
- [[remainder_decomposition_to_mod_eq]]
- [[mod_eq_symm]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1888 nodes**, depth **64**.
- Authored script length: **83 commands**.
- Runtime card: `pa lib canonical_remainders_characterize_mod_eq`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

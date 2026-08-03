---
title: "Lemma: mod_eq_bounded_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_bounded_unique`

Two balanced-congruent values below the same modulus are equal.

## Closed Peano statement

```text
forall m a b. (exists ha. ha + S a = m) -> (exists hb. hb + S b = m) -> (exists u v. a + m * u = b + m * v) -> a = b
```

## Dependencies

- [[add_comm]]
- [[division_remainder_unique]]

## Checked dependents

- [[mod_eq_to_remainder_decomposition]]
- [[mod_eq_decidable_from_remainders]]
- [[bounded_square_mod3_classify]]
- [[bounded_square_mod5_classify]]
- [[bounded_square_mod7_classify]]
- [[beta_half_range_mod_eq_value]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **961 nodes**, depth **59**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib mod_eq_bounded_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: division_remainder_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `division_remainder_exists`

Every positive divisor admits a quotient and a strictly bounded remainder.

## Closed Peano statement

```text
forall m n. ~(m = 0) -> exists q r. n = m * q + r /\ S r <= m
```

## Dependencies

- [[zero_or_succ]]
- [[division_remainder_succ]]

## Checked dependents

- [[gcd_exists_up_to]]
- [[gcd_balanced_bezout_exists_up_to]]
- [[multiple_decidable_nonzero]]
- [[mod_eq_to_remainder_decomposition]]
- [[beta_at_exists]]
- [[mod_eq_decidable_nonzero]]
- [[quadratic_residue_bounded_equiv]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **219 nodes**, depth **28**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib division_remainder_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: canonical_remainder_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_remainder_exists`

Every dividend has a canonical remainder for each nonzero modulus.

## Closed Peano statement

```text
forall m n. ~(m = 0) -> exists r. (((exists hcr_quotient_result. n = m * hcr_quotient_result + r) /\ exists hcr_gap_result. hcr_gap_result + S r = m))
```

## Dependencies

- [[division_remainder_exists]]

## Checked dependents

- [[canonical_remainder_exists_unique]]
- [[coprime_bounded_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **238 nodes**, depth **29**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib canonical_remainder_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

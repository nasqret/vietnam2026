---
title: "Lemma: canonical_remainder_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_remainder_functional`

Canonical remainders for a fixed modulus are functional whenever they exist.

## Closed Peano statement

```text
forall m n r s. (((exists hcr_quotient_result. n = m * hcr_quotient_result + r) /\ exists hcr_gap_result. hcr_gap_result + S r = m)) -> (((exists hcr_quotient_comparison. n = m * hcr_quotient_comparison + s) /\ exists hcr_gap_comparison. hcr_gap_comparison + S s = m)) -> r = s
```

## Dependencies

- [[division_remainder_unique]]

## Checked dependents

- [[canonical_remainder_exists_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **885 nodes**, depth **58**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib canonical_remainder_functional`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

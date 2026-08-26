---
title: "Lemma: canonical_remainder_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_remainder_exists_unique`

For every nonzero modulus, the canonical remainder exists uniquely; the comparison remainder is proved equal to the chosen remainder.

## Closed Peano statement

```text
forall m n. ~(m = 0) -> exists r. ((((exists hcr_quotient_unique_result. n = m * hcr_quotient_unique_result + r) /\ exists hcr_gap_unique_result. hcr_gap_unique_result + S r = m)) /\ forall s. (((exists hcr_quotient_unique_comparison. n = m * hcr_quotient_unique_comparison + s) /\ exists hcr_gap_unique_comparison. hcr_gap_unique_comparison + S s = m)) -> s = r)
```

## Dependencies

- [[canonical_remainder_exists]]
- [[canonical_remainder_functional]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1148 nodes**, depth **60**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib canonical_remainder_exists_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: canonical_remainder_zero_impossible"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `canonical_remainder_zero_impossible`

The canonical-remainder relation has no inhabitant at modulus zero.

## Closed Peano statement

```text
forall m n r. m = 0 -> ~(((exists hcr_quotient_zero_impossible. n = m * hcr_quotient_zero_impossible + r) /\ exists hcr_gap_zero_impossible. hcr_gap_zero_impossible + S r = m))
```

## Dependencies

- [[succ_ne_zero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **21 nodes**, depth **13**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib canonical_remainder_zero_impossible`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_ordered_gap_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_ordered_gap_multiple`

The directed gap between two congruent naturals is a multiple of the modulus.

## Closed Peano statement

```text
forall d k x y. k + x = y -> (exists hgcrt_mod_left_ordered_gap_assumption hgcrt_mod_right_ordered_gap_assumption. x + d * hgcrt_mod_left_ordered_gap_assumption = y + d * hgcrt_mod_right_ordered_gap_assumption) -> (exists hgcrt_divides_factor_ordered_gap_result. k = d * hgcrt_divides_factor_ordered_gap_result)
```

## Dependencies

- [[add_comm]]
- [[add_assoc]]
- [[add_left_cancel]]
- [[factor_difference]]

## Checked dependents

- [[mod_eq_lcm_merge]]

## Verification record

- Independently checked from the empty context.
- Certificate: **558 nodes**, depth **30**.
- Authored script length: **31 commands**.
- Runtime card: `pa lib mod_eq_ordered_gap_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

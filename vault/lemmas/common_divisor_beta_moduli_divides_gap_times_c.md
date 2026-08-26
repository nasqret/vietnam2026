---
title: "Lemma: common_divisor_beta_moduli_divides_gap_times_c"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `common_divisor_beta_moduli_divides_gap_times_c`

A common divisor of two ordered beta moduli divides the index gap times c.

## Closed Peano statement

```text
forall c i j gap d. j = i + gap -> (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> exists w. gap * c = d * w
```

## Dependencies

- [[divides_remainder]]
- [[add_succ_left]]
- [[add_mul]]
- [[zero_add]]

## Checked dependents

- [[beta_moduli_coprime_of_gap_dvd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **855 nodes**, depth **30**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib common_divisor_beta_moduli_divides_gap_times_c`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

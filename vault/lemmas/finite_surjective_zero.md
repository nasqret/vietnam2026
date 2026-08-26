---
title: "Lemma: finite_surjective_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_surjective_zero`

The empty decoded prefix is surjective onto the empty interval.

## Closed Peano statement

```text
forall b c n. n = 0 -> (forall fp_value_zero. (exists fp_gap_zero_value. fp_gap_zero_value + S fp_value_zero = n) -> exists fp_i_zero. ((exists fp_gap_zero_index. fp_gap_zero_index + S fp_i_zero = n) /\ (((exists ff_h_zero_entry. ff_h_zero_entry + S (fp_value_zero) = S ((S (fp_i_zero)) * c)) /\ exists ff_q_zero_entry. b = ff_q_zero_entry * S ((S (fp_i_zero)) * c) + (fp_value_zero)))))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]

## Checked dependents

- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **15**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib finite_surjective_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

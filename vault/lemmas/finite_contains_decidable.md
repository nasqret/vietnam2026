---
title: "Lemma: finite_contains_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_contains_decidable`

Occurrence of a value in a nonempty decoded prefix is constructively decidable.

## Closed Peano statement

```text
forall b c l y. ((exists fp_i_contains_l. ((exists fp_gap_contains_l_index. fp_gap_contains_l_index + S fp_i_contains_l = l) /\ (((exists ff_h_contains_l_entry. ff_h_contains_l_entry + S (y) = S ((S (fp_i_contains_l)) * c)) /\ exists ff_q_contains_l_entry. b = ff_q_contains_l_entry * S ((S (fp_i_contains_l)) * c) + (y))))) \/ ~(exists fp_i_contains_l. ((exists fp_gap_contains_l_index. fp_gap_contains_l_index + S fp_i_contains_l = l) /\ (((exists ff_h_contains_l_entry. ff_h_contains_l_entry + S (y) = S ((S (fp_i_contains_l)) * c)) /\ exists ff_q_contains_l_entry. b = ff_q_contains_l_entry * S ((S (fp_i_contains_l)) * c) + (y))))))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[finite_lt_succ_eq_or_lt]]
- [[beta_at_exists]]
- [[beta_at_unique]]
- [[eq_decidable]]
- [[le_refl]]
- [[le_succ]]

## Checked dependents

- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1961 nodes**, depth **64**.
- Authored script length: **77 commands**.
- Runtime card: `pa lib finite_contains_decidable`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

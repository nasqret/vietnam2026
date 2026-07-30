---
title: "Lemma: finite_bounded_last_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_bounded_last_succ`

A bounded successor prefix exposes a bounded final decoded value.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_i_bounded_succ. (exists fp_gap_bounded_succ_index. fp_gap_bounded_succ_index + S fp_i_bounded_succ = sn) -> exists fp_value_bounded_succ. ((((exists ff_h_bounded_succ_entry. ff_h_bounded_succ_entry + S (fp_value_bounded_succ) = S ((S (fp_i_bounded_succ)) * c)) /\ exists ff_q_bounded_succ_entry. b = ff_q_bounded_succ_entry * S ((S (fp_i_bounded_succ)) * c) + (fp_value_bounded_succ))) /\ (exists fp_gap_bounded_succ_value. fp_gap_bounded_succ_value + S fp_value_bounded_succ = sn))) -> exists x. ((((exists ff_h_last_x. ff_h_last_x + S (x) = S ((S (n)) * c)) /\ exists ff_q_last_x. b = ff_q_last_x * S ((S (n)) * c) + (x))) /\ exists h. h + S x = S n)
```

## Dependencies

- [[le_refl]]

## Checked dependents

- [[finite_last_is_top_from_prefix_surjective]]
- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **53 nodes**, depth **17**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib finite_bounded_last_succ`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

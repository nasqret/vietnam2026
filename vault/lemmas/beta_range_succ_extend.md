---
title: "Lemma: beta_range_succ_extend"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_range_succ_extend`

Recode a consecutive prefix and append its next value.

## Closed Peano statement

```text
forall b c a l sl. sl = S l -> (forall ff_i_before. (exists ff_lt_before_bound. ff_lt_before_bound + S ff_i_before = l) -> (((exists ff_h_before_decoded. ff_h_before_decoded + S (a + ff_i_before) = S ((S (ff_i_before)) * c)) /\ exists ff_q_before_decoded. b = ff_q_before_decoded * S ((S (ff_i_before)) * c) + (a + ff_i_before)))) -> exists z d. (forall ff_i_after. (exists ff_lt_after_bound. ff_lt_after_bound + S ff_i_after = sl) -> (((exists ff_h_after_decoded. ff_h_after_decoded + S (a + ff_i_after) = S ((S (ff_i_after)) * d)) /\ exists ff_q_after_decoded. z = ff_q_after_decoded * S ((S (ff_i_after)) * d) + (a + ff_i_after))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- [[beta_range_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29230 nodes**, depth **81**.
- Authored script length: **42 commands**.
- Runtime card: `pa lib beta_range_succ_extend`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

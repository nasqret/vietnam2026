---
title: "Lemma: beta_prefix_replace_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_replace_exists`

Recode a finite beta prefix while replacing one interior entry.

## Closed Peano statement

```text
forall b c i s k. (exists h. h + S i = k) -> exists z d. ((((exists ff_h_replace_entry. ff_h_replace_entry + S (s) = S ((S (i)) * d)) /\ exists ff_q_replace_entry. z = ff_q_replace_entry * S ((S (i)) * d) + (s))) /\ forall j a. (exists h. h + S j = k) -> ~(j = i) -> (((exists ff_h_replace_old. ff_h_replace_old + S (a) = S ((S (j)) * c)) /\ exists ff_q_replace_old. b = ff_q_replace_old * S ((S (j)) * c) + (a))) -> (((exists ff_h_replace_new. ff_h_replace_new + S (a) = S ((S (j)) * d)) /\ exists ff_q_replace_new. z = ff_q_replace_new * S ((S (j)) * d) + (a))))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[finite_lt_succ_eq_or_lt]]
- [[beta_prefix_extend]]
- [[beta_at_exists]]
- [[beta_at_unique]]

## Checked dependents

- [[beta_prefix_swap_last_from_entries]]

## Verification record

- Independently checked from the empty context.
- Certificate: **30981 nodes**, depth **84**.
- Authored script length: **122 commands**.
- Runtime card: `pa lib beta_prefix_replace_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: beta_repeat_entry_eq"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_repeat_entry_eq`

Every decoded entry of a Repeat prefix equals its repeated value.

## Closed Peano statement

```text
forall b c a l i x. (forall ff_i_entry. (exists ff_lt_entry_bound. ff_lt_entry_bound + S ff_i_entry = l) -> (((exists ff_h_entry_decoded. ff_h_entry_decoded + S (a) = S ((S (ff_i_entry)) * c)) /\ exists ff_q_entry_decoded. b = ff_q_entry_decoded * S ((S (ff_i_entry)) * c) + (a)))) -> (exists h. h + S i = l) -> (((exists ff_h_entry_x. ff_h_entry_x + S (x) = S ((S (i)) * c)) /\ exists ff_q_entry_x. b = ff_q_entry_x * S ((S (i)) * c) + (x))) -> x = a
```

## Dependencies

- [[beta_at_unique]]

## Checked dependents

- [[beta_repeat_transport_entry]]
- [[pow_successor_decompose]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1144 nodes**, depth **60**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib beta_repeat_entry_eq`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

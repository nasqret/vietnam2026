---
title: "Lemma: beta_range_transport_entry"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_range_transport_entry`

Two Range codes preserve every decoded entry extensionally.

## Closed Peano statement

```text
forall b c z d a l. (forall ff_i_transport_l. (exists ff_lt_transport_l_bound. ff_lt_transport_l_bound + S ff_i_transport_l = l) -> (((exists ff_h_transport_l_decoded. ff_h_transport_l_decoded + S (a + ff_i_transport_l) = S ((S (ff_i_transport_l)) * c)) /\ exists ff_q_transport_l_decoded. b = ff_q_transport_l_decoded * S ((S (ff_i_transport_l)) * c) + (a + ff_i_transport_l)))) -> (forall ff_i_transport_r. (exists ff_lt_transport_r_bound. ff_lt_transport_r_bound + S ff_i_transport_r = l) -> (((exists ff_h_transport_r_decoded. ff_h_transport_r_decoded + S (a + ff_i_transport_r) = S ((S (ff_i_transport_r)) * d)) /\ exists ff_q_transport_r_decoded. z = ff_q_transport_r_decoded * S ((S (ff_i_transport_r)) * d) + (a + ff_i_transport_r)))) -> forall i x. (exists h. h + S i = l) -> (((exists ff_h_range_transport_x. ff_h_range_transport_x + S (x) = S ((S (i)) * c)) /\ exists ff_q_range_transport_x. b = ff_q_range_transport_x * S ((S (i)) * c) + (x))) -> (((exists ff_h_range_transport_y. ff_h_range_transport_y + S (x) = S ((S (i)) * d)) /\ exists ff_q_range_transport_y. z = ff_q_range_transport_y * S ((S (i)) * d) + (x)))
```

## Dependencies

- [[beta_range_entry_eq]]

## Checked dependents

- [[factorial_functional]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1191 nodes**, depth **61**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib beta_range_transport_entry`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

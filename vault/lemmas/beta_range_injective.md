---
title: "Lemma: beta_range_injective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_range_injective`

Equal decoded values in one consecutive range have equal indices.

## Closed Peano statement

```text
forall b c a l i j x y. (forall ff_i_generic. (exists ff_lt_generic_bound. ff_lt_generic_bound + S ff_i_generic = l) -> (((exists ff_h_generic_decoded. ff_h_generic_decoded + S (a + ff_i_generic) = S ((S (ff_i_generic)) * c)) /\ exists ff_q_generic_decoded. b = ff_q_generic_decoded * S ((S (ff_i_generic)) * c) + (a + ff_i_generic)))) -> (exists gh_lt_generic_i. gh_lt_generic_i + S i = l) -> (exists gh_lt_generic_j. gh_lt_generic_j + S j = l) -> (((exists ff_h_generic_i. ff_h_generic_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_generic_i. b = ff_q_generic_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_generic_j. ff_h_generic_j + S (y) = S ((S (j)) * c)) /\ exists ff_q_generic_j. b = ff_q_generic_j * S ((S (j)) * c) + (y))) -> x = y -> i = j
```

## Dependencies

- [[beta_range_entry_eq]]
- [[add_left_cancel]]

## Checked dependents

- [[beta_half_range_mod_injective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1338 nodes**, depth **61**.
- Authored script length: **48 commands**.
- Runtime card: `pa lib beta_range_injective`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

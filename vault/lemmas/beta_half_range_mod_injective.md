---
title: "Lemma: beta_half_range_mod_injective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_half_range_mod_injective`

The odd half-range is injective modulo p at the level of indices.

## Closed Peano statement

```text
forall p h b c i j x y. p = 2 * h + 1 -> (forall gh_i_pair. (exists gh_lt_pair_bound. gh_lt_pair_bound + S gh_i_pair = h) -> (((exists gh_h_pair. gh_h_pair + S (1 + gh_i_pair) = S ((S gh_i_pair) * c)) /\ exists gh_q_pair. b = gh_q_pair * S ((S gh_i_pair) * c) + (1 + gh_i_pair)))) -> (exists gh_lt_pair_i. gh_lt_pair_i + S i = h) -> (exists gh_lt_pair_j. gh_lt_pair_j + S j = h) -> (((exists ff_h_pair_i. ff_h_pair_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_pair_i. b = ff_q_pair_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_pair_j. ff_h_pair_j + S (y) = S ((S (j)) * c)) /\ exists ff_q_pair_j. b = ff_q_pair_j * S ((S (j)) * c) + (y))) -> (exists gh_u_pair gh_v_pair. x + p * gh_u_pair = y + p * gh_v_pair) -> i = j
```

## Dependencies

- [[beta_half_range_mod_eq_value]]
- [[beta_range_injective]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4001 nodes**, depth **63**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib beta_half_range_mod_injective`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

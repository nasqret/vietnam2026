---
title: "Lemma: all_bits_prefix_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_bits_prefix_succ`

Dropping the final entry preserves the all-bits invariant.

## Closed Peano statement

```text
forall b c l sl. sl = S l -> (forall ff_i_successor. (exists ff_lt_successor_bound. ff_lt_successor_bound + S ff_i_successor = sl) -> exists ff_bit_successor. ((((exists ff_h_successor_decoded. ff_h_successor_decoded + S (ff_bit_successor) = S ((S (ff_i_successor)) * c)) /\ exists ff_q_successor_decoded. b = ff_q_successor_decoded * S ((S (ff_i_successor)) * c) + (ff_bit_successor))) /\ (ff_bit_successor = 0 \/ ff_bit_successor = 1))) -> (forall ff_i_prefix. (exists ff_lt_prefix_bound. ff_lt_prefix_bound + S ff_i_prefix = l) -> exists ff_bit_prefix. ((((exists ff_h_prefix_decoded. ff_h_prefix_decoded + S (ff_bit_prefix) = S ((S (ff_i_prefix)) * c)) /\ exists ff_q_prefix_decoded. b = ff_q_prefix_decoded * S ((S (ff_i_prefix)) * c) + (ff_bit_prefix))) /\ (ff_bit_prefix = 0 \/ ff_bit_prefix = 1)))
```

## Dependencies

- [[le_succ]]

## Checked dependents

- [[bit_count_succ_decompose]]

## Verification record

- Independently checked from the empty context.
- Certificate: **71 nodes**, depth **20**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib all_bits_prefix_succ`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

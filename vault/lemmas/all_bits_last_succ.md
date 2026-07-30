---
title: "Lemma: all_bits_last_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_bits_last_succ`

The final entry of a nonempty all-bits prefix is zero or one.

## Closed Peano statement

```text
forall b c l sl. sl = S l -> (forall ff_i_successor. (exists ff_lt_successor_bound. ff_lt_successor_bound + S ff_i_successor = sl) -> exists ff_bit_successor. ((((exists ff_h_successor_decoded. ff_h_successor_decoded + S (ff_bit_successor) = S ((S (ff_i_successor)) * c)) /\ exists ff_q_successor_decoded. b = ff_q_successor_decoded * S ((S (ff_i_successor)) * c) + (ff_bit_successor))) /\ (ff_bit_successor = 0 \/ ff_bit_successor = 1))) -> exists a. ((((exists ff_h_last. ff_h_last + S (a) = S ((S (l)) * c)) /\ exists ff_q_last. b = ff_q_last * S ((S (l)) * c) + (a))) /\ (a = 0 \/ a = 1))
```

## Dependencies

- [[le_refl]]

## Checked dependents

- [[bit_count_succ_decompose]]

## Verification record

- Independently checked from the empty context.
- Certificate: **48 nodes**, depth **15**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib all_bits_last_succ`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

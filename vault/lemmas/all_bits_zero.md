---
title: "Lemma: all_bits_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_bits_zero`

The empty decoded prefix consists only of bits, vacuously.

## Closed Peano statement

```text
forall b c l. l = 0 -> (forall ff_i_empty. (exists ff_lt_empty_bound. ff_lt_empty_bound + S ff_i_empty = l) -> exists ff_bit_empty. ((((exists ff_h_empty_decoded. ff_h_empty_decoded + S (ff_bit_empty) = S ((S (ff_i_empty)) * c)) /\ exists ff_q_empty_decoded. b = ff_q_empty_decoded * S ((S (ff_i_empty)) * c) + (ff_bit_empty))) /\ (ff_bit_empty = 0 \/ ff_bit_empty = 1)))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **15**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib all_bits_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

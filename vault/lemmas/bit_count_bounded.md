---
title: "Lemma: bit_count_bounded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bit_count_bounded`

A zero/one count never exceeds the length of its decoded prefix.

## Closed Peano statement

```text
forall b c l n. (((exists ff_u_b_sum ff_v_b_sum. ((((exists ff_h_b_sum_start. ff_h_b_sum_start + S (0) = S ((S (0)) * ff_v_b_sum)) /\ exists ff_q_b_sum_start. ff_u_b_sum = ff_q_b_sum_start * S ((S (0)) * ff_v_b_sum) + (0))) /\ ((((exists ff_h_b_sum_terminal. ff_h_b_sum_terminal + S (n) = S ((S (l)) * ff_v_b_sum)) /\ exists ff_q_b_sum_terminal. ff_u_b_sum = ff_q_b_sum_terminal * S ((S (l)) * ff_v_b_sum) + (n))) /\ forall ff_i_b_sum. (exists ff_lt_b_sum_bound. ff_lt_b_sum_bound + S ff_i_b_sum = l) -> exists ff_a_b_sum ff_r_b_sum ff_s_b_sum. ((((exists ff_h_b_sum_summand. ff_h_b_sum_summand + S (ff_a_b_sum) = S ((S (ff_i_b_sum)) * c)) /\ exists ff_q_b_sum_summand. b = ff_q_b_sum_summand * S ((S (ff_i_b_sum)) * c) + (ff_a_b_sum))) /\ ((((exists ff_h_b_sum_partial. ff_h_b_sum_partial + S (ff_r_b_sum) = S ((S (ff_i_b_sum)) * ff_v_b_sum)) /\ exists ff_q_b_sum_partial. ff_u_b_sum = ff_q_b_sum_partial * S ((S (ff_i_b_sum)) * ff_v_b_sum) + (ff_r_b_sum))) /\ ((((exists ff_h_b_sum_successor. ff_h_b_sum_successor + S (ff_s_b_sum) = S ((S (S ff_i_b_sum)) * ff_v_b_sum)) /\ exists ff_q_b_sum_successor. ff_u_b_sum = ff_q_b_sum_successor * S ((S (S ff_i_b_sum)) * ff_v_b_sum) + (ff_s_b_sum))) /\ ff_s_b_sum = ff_r_b_sum + ff_a_b_sum)))))) /\ (forall ff_i_b_bits. (exists ff_lt_b_bits_bound. ff_lt_b_bits_bound + S ff_i_b_bits = l) -> exists ff_bit_b_bits. ((((exists ff_h_b_bits_decoded. ff_h_b_bits_decoded + S (ff_bit_b_bits) = S ((S (ff_i_b_bits)) * c)) /\ exists ff_q_b_bits_decoded. b = ff_q_b_bits_decoded * S ((S (ff_i_b_bits)) * c) + (ff_bit_b_bits))) /\ (ff_bit_b_bits = 0 \/ ff_bit_b_bits = 1))))) -> exists h. h + n = l
```

## Dependencies

- [[bit_count_zero]]
- [[bit_count_succ_decompose]]
- [[add_succ_left]]
- [[add_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **3987 nodes**, depth **65**.
- Authored script length: **58 commands**.
- Runtime card: `pa lib bit_count_bounded`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

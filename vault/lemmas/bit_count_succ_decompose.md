---
title: "Lemma: bit_count_succ_decompose"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bit_count_succ_decompose`

A successor count is its prefix count plus a final zero-or-one bit.

## Closed Peano statement

```text
forall b c l sl n. sl = S l -> (((exists ff_u_successor_sum ff_v_successor_sum. ((((exists ff_h_successor_sum_start. ff_h_successor_sum_start + S (0) = S ((S (0)) * ff_v_successor_sum)) /\ exists ff_q_successor_sum_start. ff_u_successor_sum = ff_q_successor_sum_start * S ((S (0)) * ff_v_successor_sum) + (0))) /\ ((((exists ff_h_successor_sum_terminal. ff_h_successor_sum_terminal + S (n) = S ((S (sl)) * ff_v_successor_sum)) /\ exists ff_q_successor_sum_terminal. ff_u_successor_sum = ff_q_successor_sum_terminal * S ((S (sl)) * ff_v_successor_sum) + (n))) /\ forall ff_i_successor_sum. (exists ff_lt_successor_sum_bound. ff_lt_successor_sum_bound + S ff_i_successor_sum = sl) -> exists ff_a_successor_sum ff_r_successor_sum ff_s_successor_sum. ((((exists ff_h_successor_sum_summand. ff_h_successor_sum_summand + S (ff_a_successor_sum) = S ((S (ff_i_successor_sum)) * c)) /\ exists ff_q_successor_sum_summand. b = ff_q_successor_sum_summand * S ((S (ff_i_successor_sum)) * c) + (ff_a_successor_sum))) /\ ((((exists ff_h_successor_sum_partial. ff_h_successor_sum_partial + S (ff_r_successor_sum) = S ((S (ff_i_successor_sum)) * ff_v_successor_sum)) /\ exists ff_q_successor_sum_partial. ff_u_successor_sum = ff_q_successor_sum_partial * S ((S (ff_i_successor_sum)) * ff_v_successor_sum) + (ff_r_successor_sum))) /\ ((((exists ff_h_successor_sum_successor. ff_h_successor_sum_successor + S (ff_s_successor_sum) = S ((S (S ff_i_successor_sum)) * ff_v_successor_sum)) /\ exists ff_q_successor_sum_successor. ff_u_successor_sum = ff_q_successor_sum_successor * S ((S (S ff_i_successor_sum)) * ff_v_successor_sum) + (ff_s_successor_sum))) /\ ff_s_successor_sum = ff_r_successor_sum + ff_a_successor_sum)))))) /\ (forall ff_i_successor_bits. (exists ff_lt_successor_bits_bound. ff_lt_successor_bits_bound + S ff_i_successor_bits = sl) -> exists ff_bit_successor_bits. ((((exists ff_h_successor_bits_decoded. ff_h_successor_bits_decoded + S (ff_bit_successor_bits) = S ((S (ff_i_successor_bits)) * c)) /\ exists ff_q_successor_bits_decoded. b = ff_q_successor_bits_decoded * S ((S (ff_i_successor_bits)) * c) + (ff_bit_successor_bits))) /\ (ff_bit_successor_bits = 0 \/ ff_bit_successor_bits = 1))))) -> exists a r. (((exists ff_h_last. ff_h_last + S (a) = S ((S (l)) * c)) /\ exists ff_q_last. b = ff_q_last * S ((S (l)) * c) + (a))) /\ ((((exists ff_u_prefix_sum ff_v_prefix_sum. ((((exists ff_h_prefix_sum_start. ff_h_prefix_sum_start + S (0) = S ((S (0)) * ff_v_prefix_sum)) /\ exists ff_q_prefix_sum_start. ff_u_prefix_sum = ff_q_prefix_sum_start * S ((S (0)) * ff_v_prefix_sum) + (0))) /\ ((((exists ff_h_prefix_sum_terminal. ff_h_prefix_sum_terminal + S (r) = S ((S (l)) * ff_v_prefix_sum)) /\ exists ff_q_prefix_sum_terminal. ff_u_prefix_sum = ff_q_prefix_sum_terminal * S ((S (l)) * ff_v_prefix_sum) + (r))) /\ forall ff_i_prefix_sum. (exists ff_lt_prefix_sum_bound. ff_lt_prefix_sum_bound + S ff_i_prefix_sum = l) -> exists ff_a_prefix_sum ff_r_prefix_sum ff_s_prefix_sum. ((((exists ff_h_prefix_sum_summand. ff_h_prefix_sum_summand + S (ff_a_prefix_sum) = S ((S (ff_i_prefix_sum)) * c)) /\ exists ff_q_prefix_sum_summand. b = ff_q_prefix_sum_summand * S ((S (ff_i_prefix_sum)) * c) + (ff_a_prefix_sum))) /\ ((((exists ff_h_prefix_sum_partial. ff_h_prefix_sum_partial + S (ff_r_prefix_sum) = S ((S (ff_i_prefix_sum)) * ff_v_prefix_sum)) /\ exists ff_q_prefix_sum_partial. ff_u_prefix_sum = ff_q_prefix_sum_partial * S ((S (ff_i_prefix_sum)) * ff_v_prefix_sum) + (ff_r_prefix_sum))) /\ ((((exists ff_h_prefix_sum_successor. ff_h_prefix_sum_successor + S (ff_s_prefix_sum) = S ((S (S ff_i_prefix_sum)) * ff_v_prefix_sum)) /\ exists ff_q_prefix_sum_successor. ff_u_prefix_sum = ff_q_prefix_sum_successor * S ((S (S ff_i_prefix_sum)) * ff_v_prefix_sum) + (ff_s_prefix_sum))) /\ ff_s_prefix_sum = ff_r_prefix_sum + ff_a_prefix_sum)))))) /\ (forall ff_i_prefix_bits. (exists ff_lt_prefix_bits_bound. ff_lt_prefix_bits_bound + S ff_i_prefix_bits = l) -> exists ff_bit_prefix_bits. ((((exists ff_h_prefix_bits_decoded. ff_h_prefix_bits_decoded + S (ff_bit_prefix_bits) = S ((S (ff_i_prefix_bits)) * c)) /\ exists ff_q_prefix_bits_decoded. b = ff_q_prefix_bits_decoded * S ((S (ff_i_prefix_bits)) * c) + (ff_bit_prefix_bits))) /\ (ff_bit_prefix_bits = 0 \/ ff_bit_prefix_bits = 1))))) /\ ((a = 0 \/ a = 1) /\ n = r + a))
```

## Dependencies

- [[beta_sum_succ_decompose]]
- [[all_bits_prefix_succ]]
- [[all_bits_last_succ]]
- [[beta_at_unique]]

## Checked dependents

- [[bit_count_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2608 nodes**, depth **63**.
- Authored script length: **63 commands**.
- Runtime card: `pa lib bit_count_succ_decompose`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

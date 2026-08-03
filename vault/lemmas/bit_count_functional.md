---
title: "Lemma: bit_count_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bit_count_functional`

The relational count of a fixed all-bits prefix is unique.

## Closed Peano statement

```text
forall b c l n m. (((exists ff_u_l_sum ff_v_l_sum. ((((exists ff_h_l_sum_start. ff_h_l_sum_start + S (0) = S ((S (0)) * ff_v_l_sum)) /\ exists ff_q_l_sum_start. ff_u_l_sum = ff_q_l_sum_start * S ((S (0)) * ff_v_l_sum) + (0))) /\ ((((exists ff_h_l_sum_terminal. ff_h_l_sum_terminal + S (n) = S ((S (l)) * ff_v_l_sum)) /\ exists ff_q_l_sum_terminal. ff_u_l_sum = ff_q_l_sum_terminal * S ((S (l)) * ff_v_l_sum) + (n))) /\ forall ff_i_l_sum. (exists ff_lt_l_sum_bound. ff_lt_l_sum_bound + S ff_i_l_sum = l) -> exists ff_a_l_sum ff_r_l_sum ff_s_l_sum. ((((exists ff_h_l_sum_summand. ff_h_l_sum_summand + S (ff_a_l_sum) = S ((S (ff_i_l_sum)) * c)) /\ exists ff_q_l_sum_summand. b = ff_q_l_sum_summand * S ((S (ff_i_l_sum)) * c) + (ff_a_l_sum))) /\ ((((exists ff_h_l_sum_partial. ff_h_l_sum_partial + S (ff_r_l_sum) = S ((S (ff_i_l_sum)) * ff_v_l_sum)) /\ exists ff_q_l_sum_partial. ff_u_l_sum = ff_q_l_sum_partial * S ((S (ff_i_l_sum)) * ff_v_l_sum) + (ff_r_l_sum))) /\ ((((exists ff_h_l_sum_successor. ff_h_l_sum_successor + S (ff_s_l_sum) = S ((S (S ff_i_l_sum)) * ff_v_l_sum)) /\ exists ff_q_l_sum_successor. ff_u_l_sum = ff_q_l_sum_successor * S ((S (S ff_i_l_sum)) * ff_v_l_sum) + (ff_s_l_sum))) /\ ff_s_l_sum = ff_r_l_sum + ff_a_l_sum)))))) /\ (forall ff_i_l_bits. (exists ff_lt_l_bits_bound. ff_lt_l_bits_bound + S ff_i_l_bits = l) -> exists ff_bit_l_bits. ((((exists ff_h_l_bits_decoded. ff_h_l_bits_decoded + S (ff_bit_l_bits) = S ((S (ff_i_l_bits)) * c)) /\ exists ff_q_l_bits_decoded. b = ff_q_l_bits_decoded * S ((S (ff_i_l_bits)) * c) + (ff_bit_l_bits))) /\ (ff_bit_l_bits = 0 \/ ff_bit_l_bits = 1))))) -> (((exists ff_u_r_sum ff_v_r_sum. ((((exists ff_h_r_sum_start. ff_h_r_sum_start + S (0) = S ((S (0)) * ff_v_r_sum)) /\ exists ff_q_r_sum_start. ff_u_r_sum = ff_q_r_sum_start * S ((S (0)) * ff_v_r_sum) + (0))) /\ ((((exists ff_h_r_sum_terminal. ff_h_r_sum_terminal + S (m) = S ((S (l)) * ff_v_r_sum)) /\ exists ff_q_r_sum_terminal. ff_u_r_sum = ff_q_r_sum_terminal * S ((S (l)) * ff_v_r_sum) + (m))) /\ forall ff_i_r_sum. (exists ff_lt_r_sum_bound. ff_lt_r_sum_bound + S ff_i_r_sum = l) -> exists ff_a_r_sum ff_r_r_sum ff_s_r_sum. ((((exists ff_h_r_sum_summand. ff_h_r_sum_summand + S (ff_a_r_sum) = S ((S (ff_i_r_sum)) * c)) /\ exists ff_q_r_sum_summand. b = ff_q_r_sum_summand * S ((S (ff_i_r_sum)) * c) + (ff_a_r_sum))) /\ ((((exists ff_h_r_sum_partial. ff_h_r_sum_partial + S (ff_r_r_sum) = S ((S (ff_i_r_sum)) * ff_v_r_sum)) /\ exists ff_q_r_sum_partial. ff_u_r_sum = ff_q_r_sum_partial * S ((S (ff_i_r_sum)) * ff_v_r_sum) + (ff_r_r_sum))) /\ ((((exists ff_h_r_sum_successor. ff_h_r_sum_successor + S (ff_s_r_sum) = S ((S (S ff_i_r_sum)) * ff_v_r_sum)) /\ exists ff_q_r_sum_successor. ff_u_r_sum = ff_q_r_sum_successor * S ((S (S ff_i_r_sum)) * ff_v_r_sum) + (ff_s_r_sum))) /\ ff_s_r_sum = ff_r_r_sum + ff_a_r_sum)))))) /\ (forall ff_i_r_bits. (exists ff_lt_r_bits_bound. ff_lt_r_bits_bound + S ff_i_r_bits = l) -> exists ff_bit_r_bits. ((((exists ff_h_r_bits_decoded. ff_h_r_bits_decoded + S (ff_bit_r_bits) = S ((S (ff_i_r_bits)) * c)) /\ exists ff_q_r_bits_decoded. b = ff_q_r_bits_decoded * S ((S (ff_i_r_bits)) * c) + (ff_bit_r_bits))) /\ (ff_bit_r_bits = 0 \/ ff_bit_r_bits = 1))))) -> n = m
```

## Dependencies

- [[beta_sum_functional]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1488 nodes**, depth **62**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib bit_count_functional`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

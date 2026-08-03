---
title: "Lemma: bit_count_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bit_count_zero`

An empty bit prefix contains zero ones.

## Closed Peano statement

```text
forall b c l n. l = 0 -> (((exists ff_u_zero_sum ff_v_zero_sum. ((((exists ff_h_zero_sum_start. ff_h_zero_sum_start + S (0) = S ((S (0)) * ff_v_zero_sum)) /\ exists ff_q_zero_sum_start. ff_u_zero_sum = ff_q_zero_sum_start * S ((S (0)) * ff_v_zero_sum) + (0))) /\ ((((exists ff_h_zero_sum_terminal. ff_h_zero_sum_terminal + S (n) = S ((S (l)) * ff_v_zero_sum)) /\ exists ff_q_zero_sum_terminal. ff_u_zero_sum = ff_q_zero_sum_terminal * S ((S (l)) * ff_v_zero_sum) + (n))) /\ forall ff_i_zero_sum. (exists ff_lt_zero_sum_bound. ff_lt_zero_sum_bound + S ff_i_zero_sum = l) -> exists ff_a_zero_sum ff_r_zero_sum ff_s_zero_sum. ((((exists ff_h_zero_sum_summand. ff_h_zero_sum_summand + S (ff_a_zero_sum) = S ((S (ff_i_zero_sum)) * c)) /\ exists ff_q_zero_sum_summand. b = ff_q_zero_sum_summand * S ((S (ff_i_zero_sum)) * c) + (ff_a_zero_sum))) /\ ((((exists ff_h_zero_sum_partial. ff_h_zero_sum_partial + S (ff_r_zero_sum) = S ((S (ff_i_zero_sum)) * ff_v_zero_sum)) /\ exists ff_q_zero_sum_partial. ff_u_zero_sum = ff_q_zero_sum_partial * S ((S (ff_i_zero_sum)) * ff_v_zero_sum) + (ff_r_zero_sum))) /\ ((((exists ff_h_zero_sum_successor. ff_h_zero_sum_successor + S (ff_s_zero_sum) = S ((S (S ff_i_zero_sum)) * ff_v_zero_sum)) /\ exists ff_q_zero_sum_successor. ff_u_zero_sum = ff_q_zero_sum_successor * S ((S (S ff_i_zero_sum)) * ff_v_zero_sum) + (ff_s_zero_sum))) /\ ff_s_zero_sum = ff_r_zero_sum + ff_a_zero_sum)))))) /\ (forall ff_i_zero_bits. (exists ff_lt_zero_bits_bound. ff_lt_zero_bits_bound + S ff_i_zero_bits = l) -> exists ff_bit_zero_bits. ((((exists ff_h_zero_bits_decoded. ff_h_zero_bits_decoded + S (ff_bit_zero_bits) = S ((S (ff_i_zero_bits)) * c)) /\ exists ff_q_zero_bits_decoded. b = ff_q_zero_bits_decoded * S ((S (ff_i_zero_bits)) * c) + (ff_bit_zero_bits))) /\ (ff_bit_zero_bits = 0 \/ ff_bit_zero_bits = 1))))) -> n = 0
```

## Dependencies

- [[beta_sum_zero]]

## Checked dependents

- [[bit_count_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1216 nodes**, depth **61**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib bit_count_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

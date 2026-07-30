---
title: "Lemma: factorial_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factorial_zero`

The relational factorial of zero is one.

## Closed Peano statement

```text
forall n z. n = 0 -> (exists ff_b_zero ff_c_zero. ((forall ff_i_zero_range. (exists ff_lt_zero_range_bound. ff_lt_zero_range_bound + S ff_i_zero_range = n) -> (((exists ff_h_zero_range_decoded. ff_h_zero_range_decoded + S (1 + ff_i_zero_range) = S ((S (ff_i_zero_range)) * ff_c_zero)) /\ exists ff_q_zero_range_decoded. ff_b_zero = ff_q_zero_range_decoded * S ((S (ff_i_zero_range)) * ff_c_zero) + (1 + ff_i_zero_range)))) /\ (exists ff_u_zero_product ff_v_zero_product. ((((exists ff_h_zero_product_start. ff_h_zero_product_start + S (1) = S ((S (0)) * ff_v_zero_product)) /\ exists ff_q_zero_product_start. ff_u_zero_product = ff_q_zero_product_start * S ((S (0)) * ff_v_zero_product) + (1))) /\ ((((exists ff_h_zero_product_terminal. ff_h_zero_product_terminal + S (z) = S ((S (n)) * ff_v_zero_product)) /\ exists ff_q_zero_product_terminal. ff_u_zero_product = ff_q_zero_product_terminal * S ((S (n)) * ff_v_zero_product) + (z))) /\ forall ff_i_zero_product. (exists ff_lt_zero_product_bound. ff_lt_zero_product_bound + S ff_i_zero_product = n) -> exists ff_p_zero_product ff_r_zero_product ff_s_zero_product. ((((exists ff_h_zero_product_factor. ff_h_zero_product_factor + S (ff_p_zero_product) = S ((S (ff_i_zero_product)) * ff_c_zero)) /\ exists ff_q_zero_product_factor. ff_b_zero = ff_q_zero_product_factor * S ((S (ff_i_zero_product)) * ff_c_zero) + (ff_p_zero_product))) /\ ((((exists ff_h_zero_product_partial. ff_h_zero_product_partial + S (ff_r_zero_product) = S ((S (ff_i_zero_product)) * ff_v_zero_product)) /\ exists ff_q_zero_product_partial. ff_u_zero_product = ff_q_zero_product_partial * S ((S (ff_i_zero_product)) * ff_v_zero_product) + (ff_r_zero_product))) /\ ((((exists ff_h_zero_product_successor. ff_h_zero_product_successor + S (ff_s_zero_product) = S ((S (S ff_i_zero_product)) * ff_v_zero_product)) /\ exists ff_q_zero_product_successor. ff_u_zero_product = ff_q_zero_product_successor * S ((S (S ff_i_zero_product)) * ff_v_zero_product) + (ff_s_zero_product))) /\ ff_s_zero_product = ff_r_zero_product * ff_p_zero_product)))))))) -> z = 1
```

## Dependencies

- [[beta_product_zero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1223 nodes**, depth **61**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib factorial_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

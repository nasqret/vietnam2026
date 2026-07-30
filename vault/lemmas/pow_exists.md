---
title: "Lemma: pow_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_exists`

Every base and exponent have a relational finite-product power.

## Closed Peano statement

```text
forall a e. exists n. (exists ff_b_x ff_c_x. ((forall ff_i_x_repeat. (exists ff_lt_x_repeat_bound. ff_lt_x_repeat_bound + S ff_i_x_repeat = e) -> (((exists ff_h_x_repeat_decoded. ff_h_x_repeat_decoded + S (a) = S ((S (ff_i_x_repeat)) * ff_c_x)) /\ exists ff_q_x_repeat_decoded. ff_b_x = ff_q_x_repeat_decoded * S ((S (ff_i_x_repeat)) * ff_c_x) + (a)))) /\ (exists ff_u_x_product ff_v_x_product. ((((exists ff_h_x_product_start. ff_h_x_product_start + S (1) = S ((S (0)) * ff_v_x_product)) /\ exists ff_q_x_product_start. ff_u_x_product = ff_q_x_product_start * S ((S (0)) * ff_v_x_product) + (1))) /\ ((((exists ff_h_x_product_terminal. ff_h_x_product_terminal + S (n) = S ((S (e)) * ff_v_x_product)) /\ exists ff_q_x_product_terminal. ff_u_x_product = ff_q_x_product_terminal * S ((S (e)) * ff_v_x_product) + (n))) /\ forall ff_i_x_product. (exists ff_lt_x_product_bound. ff_lt_x_product_bound + S ff_i_x_product = e) -> exists ff_p_x_product ff_r_x_product ff_s_x_product. ((((exists ff_h_x_product_factor. ff_h_x_product_factor + S (ff_p_x_product) = S ((S (ff_i_x_product)) * ff_c_x)) /\ exists ff_q_x_product_factor. ff_b_x = ff_q_x_product_factor * S ((S (ff_i_x_product)) * ff_c_x) + (ff_p_x_product))) /\ ((((exists ff_h_x_product_partial. ff_h_x_product_partial + S (ff_r_x_product) = S ((S (ff_i_x_product)) * ff_v_x_product)) /\ exists ff_q_x_product_partial. ff_u_x_product = ff_q_x_product_partial * S ((S (ff_i_x_product)) * ff_v_x_product) + (ff_r_x_product))) /\ ((((exists ff_h_x_product_successor. ff_h_x_product_successor + S (ff_s_x_product) = S ((S (S ff_i_x_product)) * ff_v_x_product)) /\ exists ff_q_x_product_successor. ff_u_x_product = ff_q_x_product_successor * S ((S (S ff_i_x_product)) * ff_v_x_product) + (ff_s_x_product))) /\ ff_s_x_product = ff_r_x_product * ff_p_x_product))))))))
```

## Dependencies

- [[beta_repeat_exists]]
- [[beta_product_exists]]

## Checked dependents

- [[pow_mul_exp]]

## Verification record

- Independently checked from the empty context.
- Certificate: **59836 nodes**, depth **88**.
- Authored script length: **22 commands**.
- Runtime card: `pa lib pow_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: pow_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_one`

The relational first power of a natural is the natural itself.

## Closed Peano statement

```text
forall a e n. e = 1 -> (exists ff_b_one ff_c_one. ((forall ff_i_one_repeat. (exists ff_lt_one_repeat_bound. ff_lt_one_repeat_bound + S ff_i_one_repeat = e) -> (((exists ff_h_one_repeat_decoded. ff_h_one_repeat_decoded + S (a) = S ((S (ff_i_one_repeat)) * ff_c_one)) /\ exists ff_q_one_repeat_decoded. ff_b_one = ff_q_one_repeat_decoded * S ((S (ff_i_one_repeat)) * ff_c_one) + (a)))) /\ (exists ff_u_one_product ff_v_one_product. ((((exists ff_h_one_product_start. ff_h_one_product_start + S (1) = S ((S (0)) * ff_v_one_product)) /\ exists ff_q_one_product_start. ff_u_one_product = ff_q_one_product_start * S ((S (0)) * ff_v_one_product) + (1))) /\ ((((exists ff_h_one_product_terminal. ff_h_one_product_terminal + S (n) = S ((S (e)) * ff_v_one_product)) /\ exists ff_q_one_product_terminal. ff_u_one_product = ff_q_one_product_terminal * S ((S (e)) * ff_v_one_product) + (n))) /\ forall ff_i_one_product. (exists ff_lt_one_product_bound. ff_lt_one_product_bound + S ff_i_one_product = e) -> exists ff_p_one_product ff_r_one_product ff_s_one_product. ((((exists ff_h_one_product_factor. ff_h_one_product_factor + S (ff_p_one_product) = S ((S (ff_i_one_product)) * ff_c_one)) /\ exists ff_q_one_product_factor. ff_b_one = ff_q_one_product_factor * S ((S (ff_i_one_product)) * ff_c_one) + (ff_p_one_product))) /\ ((((exists ff_h_one_product_partial. ff_h_one_product_partial + S (ff_r_one_product) = S ((S (ff_i_one_product)) * ff_v_one_product)) /\ exists ff_q_one_product_partial. ff_u_one_product = ff_q_one_product_partial * S ((S (ff_i_one_product)) * ff_v_one_product) + (ff_r_one_product))) /\ ((((exists ff_h_one_product_successor. ff_h_one_product_successor + S (ff_s_one_product) = S ((S (S ff_i_one_product)) * ff_v_one_product)) /\ exists ff_q_one_product_successor. ff_u_one_product = ff_q_one_product_successor * S ((S (S ff_i_one_product)) * ff_v_one_product) + (ff_s_one_product))) /\ ff_s_one_product = ff_r_one_product * ff_p_one_product)))))))) -> n = a
```

## Dependencies

- [[pow_one_from_zero_successor]]

## Checked dependents

- [[pow_two_from_one_successor]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3856 nodes**, depth **65**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib pow_one`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: pow_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_two`

The relational second power is exactly the square.

## Closed Peano statement

```text
forall a e n. e = 2 -> (exists ff_b_two ff_c_two. ((forall ff_i_two_repeat. (exists ff_lt_two_repeat_bound. ff_lt_two_repeat_bound + S ff_i_two_repeat = e) -> (((exists ff_h_two_repeat_decoded. ff_h_two_repeat_decoded + S (a) = S ((S (ff_i_two_repeat)) * ff_c_two)) /\ exists ff_q_two_repeat_decoded. ff_b_two = ff_q_two_repeat_decoded * S ((S (ff_i_two_repeat)) * ff_c_two) + (a)))) /\ (exists ff_u_two_product ff_v_two_product. ((((exists ff_h_two_product_start. ff_h_two_product_start + S (1) = S ((S (0)) * ff_v_two_product)) /\ exists ff_q_two_product_start. ff_u_two_product = ff_q_two_product_start * S ((S (0)) * ff_v_two_product) + (1))) /\ ((((exists ff_h_two_product_terminal. ff_h_two_product_terminal + S (n) = S ((S (e)) * ff_v_two_product)) /\ exists ff_q_two_product_terminal. ff_u_two_product = ff_q_two_product_terminal * S ((S (e)) * ff_v_two_product) + (n))) /\ forall ff_i_two_product. (exists ff_lt_two_product_bound. ff_lt_two_product_bound + S ff_i_two_product = e) -> exists ff_p_two_product ff_r_two_product ff_s_two_product. ((((exists ff_h_two_product_factor. ff_h_two_product_factor + S (ff_p_two_product) = S ((S (ff_i_two_product)) * ff_c_two)) /\ exists ff_q_two_product_factor. ff_b_two = ff_q_two_product_factor * S ((S (ff_i_two_product)) * ff_c_two) + (ff_p_two_product))) /\ ((((exists ff_h_two_product_partial. ff_h_two_product_partial + S (ff_r_two_product) = S ((S (ff_i_two_product)) * ff_v_two_product)) /\ exists ff_q_two_product_partial. ff_u_two_product = ff_q_two_product_partial * S ((S (ff_i_two_product)) * ff_v_two_product) + (ff_r_two_product))) /\ ((((exists ff_h_two_product_successor. ff_h_two_product_successor + S (ff_s_two_product) = S ((S (S ff_i_two_product)) * ff_v_two_product)) /\ exists ff_q_two_product_successor. ff_u_two_product = ff_q_two_product_successor * S ((S (S ff_i_two_product)) * ff_v_two_product) + (ff_s_two_product))) /\ ff_s_two_product = ff_r_two_product * ff_p_two_product)))))))) -> n = a * a
```

## Dependencies

- [[pow_two_from_one_successor]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6460 nodes**, depth **68**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib pow_two`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

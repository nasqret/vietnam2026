---
title: "Lemma: beta_product_replace_balance"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_replace_balance`

Replacing one factor balances the old and new finite products by the exchanged values.

## Closed Peano statement

```text
forall k b c z d i x y p q. (exists h. h + S i = k) -> (((exists ff_h_balance_old_i. ff_h_balance_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_balance_old_i. b = ff_q_balance_old_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_balance_new_i. ff_h_balance_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_balance_new_i. z = ff_q_balance_new_i * S ((S (i)) * d) + (y))) -> (forall j a. (exists h. h + S j = k) -> ~(j = i) -> (((exists ff_h_balance_old_j. ff_h_balance_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_balance_old_j. b = ff_q_balance_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_balance_new_j. ff_h_balance_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_balance_new_j. z = ff_q_balance_new_j * S ((S (j)) * d) + (a)))) -> (exists ff_u_balance_old ff_v_balance_old. ((((exists ff_h_balance_old_start. ff_h_balance_old_start + S (1) = S ((S (0)) * ff_v_balance_old)) /\ exists ff_q_balance_old_start. ff_u_balance_old = ff_q_balance_old_start * S ((S (0)) * ff_v_balance_old) + (1))) /\ ((((exists ff_h_balance_old_terminal. ff_h_balance_old_terminal + S (p) = S ((S (k)) * ff_v_balance_old)) /\ exists ff_q_balance_old_terminal. ff_u_balance_old = ff_q_balance_old_terminal * S ((S (k)) * ff_v_balance_old) + (p))) /\ forall ff_i_balance_old. (exists ff_lt_balance_old_bound. ff_lt_balance_old_bound + S ff_i_balance_old = k) -> exists ff_p_balance_old ff_r_balance_old ff_s_balance_old. ((((exists ff_h_balance_old_factor. ff_h_balance_old_factor + S (ff_p_balance_old) = S ((S (ff_i_balance_old)) * c)) /\ exists ff_q_balance_old_factor. b = ff_q_balance_old_factor * S ((S (ff_i_balance_old)) * c) + (ff_p_balance_old))) /\ ((((exists ff_h_balance_old_partial. ff_h_balance_old_partial + S (ff_r_balance_old) = S ((S (ff_i_balance_old)) * ff_v_balance_old)) /\ exists ff_q_balance_old_partial. ff_u_balance_old = ff_q_balance_old_partial * S ((S (ff_i_balance_old)) * ff_v_balance_old) + (ff_r_balance_old))) /\ ((((exists ff_h_balance_old_successor. ff_h_balance_old_successor + S (ff_s_balance_old) = S ((S (S ff_i_balance_old)) * ff_v_balance_old)) /\ exists ff_q_balance_old_successor. ff_u_balance_old = ff_q_balance_old_successor * S ((S (S ff_i_balance_old)) * ff_v_balance_old) + (ff_s_balance_old))) /\ ff_s_balance_old = ff_r_balance_old * ff_p_balance_old)))))) -> (exists ff_u_balance_new ff_v_balance_new. ((((exists ff_h_balance_new_start. ff_h_balance_new_start + S (1) = S ((S (0)) * ff_v_balance_new)) /\ exists ff_q_balance_new_start. ff_u_balance_new = ff_q_balance_new_start * S ((S (0)) * ff_v_balance_new) + (1))) /\ ((((exists ff_h_balance_new_terminal. ff_h_balance_new_terminal + S (q) = S ((S (k)) * ff_v_balance_new)) /\ exists ff_q_balance_new_terminal. ff_u_balance_new = ff_q_balance_new_terminal * S ((S (k)) * ff_v_balance_new) + (q))) /\ forall ff_i_balance_new. (exists ff_lt_balance_new_bound. ff_lt_balance_new_bound + S ff_i_balance_new = k) -> exists ff_p_balance_new ff_r_balance_new ff_s_balance_new. ((((exists ff_h_balance_new_factor. ff_h_balance_new_factor + S (ff_p_balance_new) = S ((S (ff_i_balance_new)) * d)) /\ exists ff_q_balance_new_factor. z = ff_q_balance_new_factor * S ((S (ff_i_balance_new)) * d) + (ff_p_balance_new))) /\ ((((exists ff_h_balance_new_partial. ff_h_balance_new_partial + S (ff_r_balance_new) = S ((S (ff_i_balance_new)) * ff_v_balance_new)) /\ exists ff_q_balance_new_partial. ff_u_balance_new = ff_q_balance_new_partial * S ((S (ff_i_balance_new)) * ff_v_balance_new) + (ff_r_balance_new))) /\ ((((exists ff_h_balance_new_successor. ff_h_balance_new_successor + S (ff_s_balance_new) = S ((S (S ff_i_balance_new)) * ff_v_balance_new)) /\ exists ff_q_balance_new_successor. ff_u_balance_new = ff_q_balance_new_successor * S ((S (S ff_i_balance_new)) * ff_v_balance_new) + (ff_s_balance_new))) /\ ff_s_balance_new = ff_r_balance_new * ff_p_balance_new)))))) -> q * x = p * y
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[finite_lt_succ_eq_or_lt]]
- [[beta_product_succ_decompose]]
- [[beta_product_transport_prefix]]
- [[beta_product_functional]]
- [[beta_at_unique]]
- [[mul_assoc]]
- [[mul_comm]]
- [[le_succ]]
- [[le_refl]]
- [[lt_irrefl_expanded]]

## Checked dependents

- [[beta_product_swap_last_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **4780 nodes**, depth **66**.
- Authored script length: **202 commands**.
- Runtime card: `pa lib beta_product_replace_balance`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

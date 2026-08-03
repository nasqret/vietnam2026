---
title: "Lemma: beta_prefix_swap_last_reflect"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_swap_last_reflect`

Every decoded swapped entry reflects to one of the two moved entries or the original index.

## Closed Peano statement

```text
forall b c z d n i x y. (((exists ff_h_reflect_new_i. ff_h_reflect_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_reflect_new_i. z = ff_q_reflect_new_i * S ((S (i)) * d) + (y))) -> (((exists ff_h_reflect_new_n. ff_h_reflect_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_reflect_new_n. z = ff_q_reflect_new_n * S ((S (n)) * d) + (x))) -> (forall k v. (exists h. h + S k = S n) -> ~(k = i) -> ~(k = n) -> (((exists ff_h_reflect_old_k. ff_h_reflect_old_k + S (v) = S ((S (k)) * c)) /\ exists ff_q_reflect_old_k. b = ff_q_reflect_old_k * S ((S (k)) * c) + (v))) -> (((exists ff_h_reflect_new_k. ff_h_reflect_new_k + S (v) = S ((S (k)) * d)) /\ exists ff_q_reflect_new_k. z = ff_q_reflect_new_k * S ((S (k)) * d) + (v)))) -> forall j a. (exists h. h + S j = S n) -> (((exists ff_h_reflect_new_j. ff_h_reflect_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_reflect_new_j. z = ff_q_reflect_new_j * S ((S (j)) * d) + (a))) -> ((j = i /\ a = y) \/ ((j = n /\ a = x) \/ (~(j = i) /\ (~(j = n) /\ (((exists ff_h_reflect_old_j. ff_h_reflect_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_reflect_old_j. b = ff_q_reflect_old_j * S ((S (j)) * c) + (a)))))))
```

## Dependencies

- [[eq_decidable]]
- [[beta_at_exists]]
- [[beta_at_unique]]

## Checked dependents

- [[finite_swap_last_injective]]
- [[finite_swap_last_surjective_back]]
- [[beta_reindex_alignment_swap_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1765 nodes**, depth **62**.
- Authored script length: **77 commands**.
- Runtime card: `pa lib beta_prefix_swap_last_reflect`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: quadratic_residue_search_up_to"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `quadratic_residue_search_up_to`

Inclusive bounded search constructively decides square congruence.

## Closed Peano statement

```text
forall B p a. ~(p = 0) -> ((exists qr_x_search_yes. (exists qr_bound_search_yes. qr_bound_search_yes + qr_x_search_yes = B) /\ (exists qr_u_search_yes qr_v_search_yes. qr_x_search_yes * qr_x_search_yes + p * qr_u_search_yes = a + p * qr_v_search_yes)) \/ (forall qr_x_search_no. (exists qr_bound_search_no. qr_bound_search_no + qr_x_search_no = B) -> ~(exists qr_u_search_no qr_v_search_no. qr_x_search_no * qr_x_search_no + p * qr_u_search_no = a + p * qr_v_search_no)))
```

## Dependencies

- [[mod_eq_decidable_nonzero]]
- [[add_eq_zero_right]]
- [[le_eq_or_lt]]
- [[add_succ_left]]
- [[zero_add]]

## Checked dependents

- [[quadratic_residue_bounded_decidable_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2480 nodes**, depth **68**.
- Authored script length: **91 commands**.
- Runtime card: `pa lib quadratic_residue_search_up_to`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

---
title: "Lemma: mod_eq_decidable_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_decidable_nonzero`

Balanced congruence is constructively decidable at nonzero modulus.

## Closed Peano statement

```text
forall p a b. ~(p = 0) -> (exists qr_u_dec_yes qr_v_dec_yes. a + p * qr_u_dec_yes = b + p * qr_v_dec_yes) \/ ~(exists qr_u_dec_no qr_v_dec_no. a + p * qr_u_dec_no = b + p * qr_v_dec_no)
```

## Dependencies

- [[division_remainder_exists]]
- [[mul_comm]]
- [[mod_eq_decidable_from_remainders]]

## Checked dependents

- [[quadratic_residue_search_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2189 nodes**, depth **67**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib mod_eq_decidable_nonzero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

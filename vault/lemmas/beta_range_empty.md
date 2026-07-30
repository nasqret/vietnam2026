---
title: "Lemma: beta_range_empty"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_range_empty`

Every consecutive beta range of length zero is vacuous.

## Closed Peano statement

```text
forall b c a l. l = 0 -> (forall ff_i_empty. (exists ff_lt_empty_bound. ff_lt_empty_bound + S ff_i_empty = l) -> (((exists ff_h_empty_decoded. ff_h_empty_decoded + S (a + ff_i_empty) = S ((S (ff_i_empty)) * c)) /\ exists ff_q_empty_decoded. b = ff_q_empty_decoded * S ((S (ff_i_empty)) * c) + (a + ff_i_empty))))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]

## Checked dependents

- [[beta_range_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **42 nodes**, depth **16**.
- Authored script length: **18 commands**.
- Runtime card: `pa lib beta_range_empty`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

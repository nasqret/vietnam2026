---
title: "Lemma: beta_range_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_range_exists`

Every start and length admit a beta-coded consecutive range.

## Closed Peano statement

```text
forall a l. exists b c. (forall ff_i_r. (exists ff_lt_r_bound. ff_lt_r_bound + S ff_i_r = l) -> (((exists ff_h_r_decoded. ff_h_r_decoded + S (a + ff_i_r) = S ((S (ff_i_r)) * c)) /\ exists ff_q_r_decoded. b = ff_q_r_decoded * S ((S (ff_i_r)) * c) + (a + ff_i_r))))
```

## Dependencies

- [[beta_range_empty]]
- [[beta_range_succ_extend]]

## Checked dependents

- [[factorial_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29328 nodes**, depth **83**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib beta_range_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

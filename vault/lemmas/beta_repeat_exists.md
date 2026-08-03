---
title: "Lemma: beta_repeat_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_repeat_exists`

Every value and length admit a beta-coded constant prefix.

## Closed Peano statement

```text
forall a l. exists b c. (forall ff_i_r. (exists ff_lt_r_bound. ff_lt_r_bound + S ff_i_r = l) -> (((exists ff_h_r_decoded. ff_h_r_decoded + S (a) = S ((S (ff_i_r)) * c)) /\ exists ff_q_r_decoded. b = ff_q_r_decoded * S ((S (ff_i_r)) * c) + (a))))
```

## Dependencies

- [[beta_repeat_empty]]
- [[beta_repeat_succ_extend]]

## Checked dependents

- [[pow_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29322 nodes**, depth **83**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib beta_repeat_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

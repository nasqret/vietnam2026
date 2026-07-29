---
title: "Lemma: all_prime_succ_intro"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_prime_succ_intro`

Append one explicitly decoded prime to an AllPrime prefix.

## Closed Peano statement

```text
forall b c l p. (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1)) -> (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1)))
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- [[beta_prefix_extend_all_prime]]
- [[beta_canonical_append_empty]]
- [[beta_canonical_append_succ]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **150 nodes**, depth **21**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib all_prime_succ_intro`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

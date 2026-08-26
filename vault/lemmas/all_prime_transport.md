---
title: "Lemma: all_prime_transport"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_prime_transport`

Transport AllPrime across pointwise value-preserving beta recoding.

## Closed Peano statement

```text
forall b c z d l. (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i p. (exists h. h + S i = l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) -> ((exists h. h + S p = S ((S i) * d)) /\ exists w. z = w * S ((S i) * d) + p)) -> (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * d)) /\ exists w. z = w * S ((S i) * d) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1)))
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_prefix_extend_all_prime]]
- [[beta_canonical_append_succ]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **26 nodes**, depth **17**.
- Authored script length: **23 commands**.
- Runtime card: `pa lib all_prime_transport`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

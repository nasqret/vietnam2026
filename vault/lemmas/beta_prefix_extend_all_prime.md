---
title: "Lemma: beta_prefix_extend_all_prime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_extend_all_prime`

Recode a beta prefix, preserve all old primes, and append one exact prime.

## Closed Peano statement

```text
forall k b e s. (forall i. (exists h. h + S i = k) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. b = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (~(s = 1) /\ forall a d. s = a * d -> a = 1 \/ d = 1) -> exists z c. ((((exists h. h + S s = S ((S k) * c)) /\ exists w. z = w * S ((S k) * c) + s) /\ forall i a. (exists h. h + S i = k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. b = w * S ((S i) * e) + a) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + a)) /\ (forall i. (exists h. h + S i = S k) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[all_prime_transport]]
- [[all_prime_succ_intro]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **29280 nodes**, depth **81**.
- Authored script length: **39 commands**.
- Runtime card: `pa lib beta_prefix_extend_all_prime`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

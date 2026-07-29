---
title: "Lemma: sorted_transport"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `sorted_transport`

Transport Sorted across pointwise value-preserving beta recoding.

## Closed Peano statement

```text
forall b c z d l. (forall i. (exists h. h + S (S i) = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))) -> (forall i p. (exists h. h + S i = l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) -> ((exists h. h + S p = S ((S i) * d)) /\ exists w. z = w * S ((S i) * d) + p)) -> (forall i. (exists h. h + S (S i) = l) -> exists p q. (((exists h. h + S p = S ((S i) * d)) /\ exists w. z = w * S ((S i) * d) + p) /\ (((exists h. h + S q = S ((S S i) * d)) /\ exists w. z = w * S ((S S i) * d) + q) /\ (exists h. h + p = q))))
```

## Dependencies

- [[lt_to_le]]

## Checked dependents

- [[beta_prefix_extend_sorted_succ]]
- [[beta_canonical_append_succ]]
- [[beta_canonical_append_general]]

## Verification record

- Independently checked from the empty context.
- Certificate: **89 nodes**, depth **21**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib sorted_transport`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

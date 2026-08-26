---
title: "Lemma: beta_prefix_extend_sorted_singleton"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_extend_sorted_singleton`

Append the first value to an empty code; the resulting singleton is Sorted.

## Closed Peano statement

```text
forall b e s. exists z c. ((((exists h. h + S s = S ((S 0) * c)) /\ exists w. z = w * S ((S 0) * c) + s) /\ forall i a. (exists h. h + S i = 0) -> ((exists h. h + S a = S ((S i) * e)) /\ exists w. b = w * S ((S i) * e) + a) -> ((exists h. h + S a = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + a)) /\ (forall i. (exists h. h + S (S i) = 1) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. z = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. z = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))))
```

## Dependencies

- [[beta_prefix_extend]]
- [[sorted_singleton]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **29146 nodes**, depth **81**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib beta_prefix_extend_sorted_singleton`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

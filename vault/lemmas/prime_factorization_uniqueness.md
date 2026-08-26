---
title: "Lemma: prime_factorization_uniqueness"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_factorization_uniqueness`

Exact catalog finite prime-factorization uniqueness target.

## Closed Peano statement

```text
forall n l b c m d e. (((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists w. u = w * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = l) -> exists p q. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (((exists h. h + S q = S ((S S i) * c)) /\ exists w. b = w * S ((S S i) * c) + q) /\ (exists h. h + p = q)))))) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists w. u = w * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S m) * v)) /\ exists w. u = w * S ((S m) * v) + n) /\ forall i. (exists h. h + S i = m) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists w. u = w * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists w. u = w * S ((S S i) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = m) -> exists p. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S S i = m) -> exists p q. (((exists h. h + S p = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + p) /\ (((exists h. h + S q = S ((S S i) * e)) /\ exists w. d = w * S ((S S i) * e) + q) /\ (exists h. h + p = q))))))) -> (l = m /\ forall i p q. (exists h. h + S i = l) -> ((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) -> ((exists h. h + S q = S ((S i) * e)) /\ exists w. d = w * S ((S i) * e) + q) -> p = q)
```

## Dependencies

- [[prime_factorization_uniqueness_by_length]]

## Checked dependents

- [[fundamental_theorem_of_arithmetic]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29789 nodes**, depth **82**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib prime_factorization_uniqueness`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

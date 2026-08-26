---
title: "Lemma: fundamental_theorem_of_arithmetic"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `fundamental_theorem_of_arithmetic`

Native beta-coded prime-factorization existence and uniqueness in first-order PA; no conventional list primitive and no DNE.

## Closed Peano statement

```text
(forall n. ~(n = 0) -> exists l b c. ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S (S i)) * v)) /\ exists q. u = q * S ((S (S i)) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S (p) = S ((S (i)) * c)) /\ exists w. b = w * S ((S (i)) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S (S i) = l) -> exists p q. (((exists h. h + S (p) = S ((S (i)) * c)) /\ exists w. b = w * S ((S (i)) * c) + p) /\ (((exists h. h + S (q) = S ((S (S i)) * c)) /\ exists w. b = w * S ((S (S i)) * c) + q) /\ exists h. h + p = q)))))) /\ (forall n l b c m d e. (((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S l) * v)) /\ exists q. u = q * S ((S l) * v) + n) /\ forall i. (exists h. h + S i = l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S (S i)) * v)) /\ exists q. u = q * S ((S (S i)) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S (p) = S ((S (i)) * c)) /\ exists w. b = w * S ((S (i)) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S (S i) = l) -> exists p q. (((exists h. h + S (p) = S ((S (i)) * c)) /\ exists w. b = w * S ((S (i)) * c) + p) /\ (((exists h. h + S (q) = S ((S (S i)) * c)) /\ exists w. b = w * S ((S (S i)) * c) + q) /\ exists h. h + p = q))))) /\ ((exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S m) * v)) /\ exists q. u = q * S ((S m) * v) + n) /\ forall i. (exists h. h + S i = m) -> exists p r s. (((exists h. h + S p = S ((S i) * e)) /\ exists q. d = q * S ((S i) * e) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S (S i)) * v)) /\ exists q. u = q * S ((S (S i)) * v) + s) /\ s = r * p)))))) /\ ((forall i. (exists h. h + S i = m) -> exists p. (((exists h. h + S (p) = S ((S (i)) * e)) /\ exists w. d = w * S ((S (i)) * e) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) /\ (forall i. (exists h. h + S (S i) = m) -> exists p q. (((exists h. h + S (p) = S ((S (i)) * e)) /\ exists w. d = w * S ((S (i)) * e) + p) /\ (((exists h. h + S (q) = S ((S (S i)) * e)) /\ exists w. d = w * S ((S (S i)) * e) + q) /\ exists h. h + p = q)))))) -> (l = m /\ forall i p q. (exists h. h + S i = l) -> ((exists h. h + S (p) = S ((S (i)) * c)) /\ exists w. b = w * S ((S (i)) * c) + p) -> ((exists h. h + S (q) = S ((S (i)) * e)) /\ exists w. d = w * S ((S (i)) * e) + q) -> p = q))
```

## Dependencies

- [[prime_factorization_existence]]
- [[prime_factorization_uniqueness]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **73767 nodes**, depth **99**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib fundamental_theorem_of_arithmetic`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]

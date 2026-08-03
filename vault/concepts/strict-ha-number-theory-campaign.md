---
title: Strict HA number-theory campaign
aliases:
  - HA number theory campaign
  - canonical arithmetic campaign
tags:
  - peano-lab
  - number-theory
  - heyting-arithmetic
---

# Strict HA number-theory campaign

The campaign builds canonical, reusable interfaces in first-order
intuitionistic arithmetic without extending Peano Lab's object language.

## Evidence boundary

- `public_checked`: an empty-context certificate checks and the theorem was
  deliberately enrolled in the public registry.
- `closed_checked_candidate`: an empty-context certificate checks, but the
  theorem remains isolated.
- a checked dependency-curried body is weaker than either status.

The current registry has 393 theorems. Nine strict-HA tranche-01 interfaces are
public; three canonical-gcd and 60 signed representation, normalization,
negation, addition, and multiplication theorems remain closed candidates.
Thus the isolated corpus has 63 total candidates and the campaign records 72
theorem receipts. The definition freeze remains 45 API rows over 44 distinct
public theorems, and the catalog remains 394 entries; the latest D06 work
grants no admission.

## Dependency spine

```mermaid
flowchart TD
  D[division with remainder] --> R[canonical remainder]
  R --> C[canonical congruence bridge]
  C --> I[bounded modular inverse criterion]
  G[relational IsGCD] --> CG[canonical gcd candidate]
  P[K1-only parity separation candidate] --> S[canonical signed decoder candidates]
  S --> E[decoded-code extensionality]
  S --> N[balanced-pair normalization]
  E --> N
  N --> G[signed negation]
  N --> A[signed addition core]
  G --> L[signed addition laws]
  A --> L
  L --> M[signed multiplication core and complete algebra]
  M --> D7[D07 natural scaling]
  D7 --> B[signed Bezout bridge]
```

The signed representation is parity-interleaved:

$$
p\mapsto 2p,\qquad -(k+1)\mapsto 2k+1.
$$

It has a unique zero and does not depend on division, CRT, Gödel-β coding,
or the future pair/list representation.

The K3 seed closes the elementary even/odd separation, the seven decoder
theorems, literal-code/cross-sum extensionality in both directions, and total,
extensional, functional `SignedBalance` normalization with an exact zero
criterion. Negation is now total, functional, symmetric, fixes zero, and is
involutive. `SignedAdd` now has exact decoded-equation introduction and
elimination, totality, and literal-output functionality. The largest signed
certificate is currently `signed_add_functional` at 1,754 structural nodes,
depth 38, and 34 Cuts. Addition is now commutative, has two-sided zero, and
sums with canonical negation to zero in both orientations. A generic cross-sum
composition helper now also closes graph associativity. None is public yet.
The five-row `SignedMul` core now has decoder bridges, totality, and literal
output functionality. Its largest certificate is `signed_mul_functional` at
1,808 nodes, depth 40, and 34 Cuts. Five further candidates prove graph
commutativity, two-sided zero annihilation, and the two-sided identity law for
signed positive-one code `2`. The largest new certificate is
`signed_mul_one_right` at 745 nodes, depth 43, and 18 Cuts. The four-row
[`SignedMul` associativity tranche](../../peano-lab/py/peano_lab/library/ha_signed_mul_associative_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_mul_associative_candidate.py)
now close the pair-transport, component-association, decoded-equation, and
graph laws. The seven-row
[`distributivity tranche`](../../peano-lab/py/peano_lab/library/ha_signed_mul_distributive_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_mul_distributive_candidate.py)
close left and right distributivity through reusable balanced-sum helpers.
The right-distributive endpoint is the largest new certificate at 3,717
nodes, depth 60, and 53 Cuts. Two cold closures agree on the complete 60-row
signed-stack digest
`7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd`.
The complete D06 elementary signed algebra is therefore closed at candidate
status. D07 natural scaling is next.

The independent pair/cell design is now frozen in `HA-K3-PAIR-1` using the
doubled Cantor polynomial and a successor cell tag. This does not close the
list layer: variable-length tail iteration still needs an independently
selected computation-history representation. Pairing alone yields only a
fixed-length formula schema.

## Repository anchors

- `research/arithmetic-library/ha-number-theory-campaign.json`
- `research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md`
- `research/arithmetic-library/ha-canonical-pair-cell-rfc-v1.md`
- `PLAN/12_ha_number_theory_campaign.md`
- `book/arithmetic-library/strict-ha-campaign.md`

## Related notes

- [[arithmetic-library-moc]]
- [[peano-lab]]
- [[proof-certificate]]
- [[intuitionistic-logic]]

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
public. The isolated corpus now has 109 candidates and the campaign records
118 theorem receipts across 21 candidate modules and 22 focused tests. Its
strict-K3 component remains exactly 74 signed representation, normalization,
arithmetic, natural-scale, and Bezout-bridge rows across 16 modules. The K4
remainder consists of three canonical-gcd package rows, one signed-gcd client,
five canonical-gcd edge rows, 17 relational-LCM rows, and nine checked
gcd--LCM totality/compatibility rows. The definition freeze remains 45 API
rows over 44 distinct public theorems, there are 56 public references, and the
catalog remains 394 entries. None of the new gcd/LCM rows is admitted.

## Dependency spine

```mermaid
flowchart TD
  D[division with remainder] --> R[canonical remainder]
  R --> C[canonical congruence bridge]
  C --> I[bounded modular inverse criterion]
  subgraph K3[Strict K3 signed stack — 74 rows]
    P[K1-only parity separation] --> S[canonical signed decoder]
    S --> E[decoded-code extensionality]
    S --> N[balanced-pair normalization]
    E --> N
    N --> SN[signed negation]
    N --> A[signed addition core]
    SN --> AL[signed addition laws]
    A --> AL
    AL --> M[signed multiplication and complete algebra]
    M --> D7[D07 natural scaling]
    D7 --> SB[D08 signed Bezout bridge]
  end
  subgraph K4[K4 gcd and LCM clients]
    D --> RG
    RG[public relational gcd + balanced Bezout] --> CG[canonical gcd package]
    CG --> GE[canonical gcd edge laws — 5 rows]
    RG --> SG[K4 signed gcd and Bezout client]
    SB --> SG
    RL[relational IsLCM API — 17 rows] --> BF[A–E algebraic bridge]
    RG --> BF
    BF --> CE[F compatible gcd/LCM existence]
    CE --> LT[G relational LCM totality]
    LT --> LU[H unique LCM value]
    CE --> GP[I gcd–LCM product]
    LU --> GP
  end
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
status. The five-row
[`SignedNatScale` core](../../peano-lab/py/peano_lab/library/ha_signed_nat_scale_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_nat_scale_candidate.py)
identify the graph with the decoded equation
`scale*ip+on = scale*inn+op`, prove both directions, and close totality and
literal-output functionality. Their 65-row signed-stack digest is
`511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331`.
The five-row
[`natural-scale law tranche`](../../peano-lab/py/peano_lab/library/ha_signed_nat_scale_laws_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_nat_scale_laws_candidate.py)
then prove generic left-scaling transport, decoded-equation composition,
`SignedNatScale(0,input,0)`, `SignedNatScale(1,input,input)`, and the exact
inner-then-outer graph law
`SignedNatScale(inner,input,middle) -> SignedNatScale(outer,middle,output) ->
SignedNatScale(outer*inner,input,output)`. The direct composition helper was
chosen over treating D07 as `SignedMul(2*scale,input,output)`: that D06 alias
would add an unnecessary signed-coercion dependency to the D08 Bezout path.
The complete 70-row signed-stack digest is
`81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d`.
D07 is closed at candidate status. The four-row
[`SignedBezout` bridge](../../peano-lab/py/peano_lab/library/ha_signed_bezout_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_bezout_candidate.py)
now prove that the legacy four-natural `BalancedBezout` relation holds exactly
when canonical signed coefficient codes exist. The proof normalizes `(xp,xn)`
and `(yp,yn)` independently while respecting the legacy witness order
`xp,yp,xn,yn`; it intentionally proves no uniqueness of the coefficient pair.
Two cold closures agree on the complete 74-row signed-stack digest
`b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
D08 is closed at candidate status with 74 signed/77 total candidates, 86
receipts, 16 K3 modules, and 18 focused tests. Its strict closure reaches no
division, remainder, CRT, beta, classical, or DNE theorem. The gcd packaging
client remains separate in K4 and no D08 row is public.

The one-row
[`K4 signed-gcd client`](../../peano-lab/py/peano_lab/library/ha_signed_bezout_gcd_candidate.py)
and its
[`focused audit`](../../peano-lab/py/tests/test_ha_signed_bezout_gcd_candidate.py)
now combine the public relational-gcd/balanced-Bezout theorem with D08. The
certificate has 3,535 nodes, depth 48, and 74 Cuts, with digest
`4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3`.
Its closure intentionally reaches the Euclidean division chain; the manifest
therefore records an explicit `K3 -> K4` layer edge. It does not change the
strict 74-row K3 digest.

The canonical gcd/LCM checkpoint is now closed at candidate status. The
five-row
[`canonical-gcd edge tranche`](../../peano-lab/py/peano_lab/library/ha_canonical_gcd_edges_candidate.py)
pins zero, one, and swap functionality. The 17-row
[`relational-LCM tranche`](../../peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py)
implements the universal property, projections, leastness, uniqueness,
divisibility, product-bound, self/one, and forced-zero laws. Its literal-safe
expander accepts exactly identifiers and the reviewed literals `0` and `1`;
zero-left is derived from the direct zero-right theorem by symmetry.

The nine-row
[`gcd--LCM bridge`](../../peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py)
then follows the checked path

```text
balanced Bezout + relational gcd
  -> coprime quotient factors
  -> product LCM + nonzero scaling
  -> compatible gcd/LCM pair
  -> LCM totality
  -> unique LCM value
  -> gcd * lcm = input product.
```

The compatible-pair certificate has 9,038 nodes at depth 60; the final
`gcd_lcm_product` certificate has 10,441 nodes at depth 61. Both zero and
nonzero branches are mutation-audited, every bridge certificate has zero
`DNE` nodes, and all rows remain unregistered. The complete isolated corpus is
109 candidates and 118 receipts across 21 modules and 22 focused tests. The
strict K3 stack remains 74 rows; public registry/reference/freeze/catalog
counts remain 393/56/45-over-44/394.

The independent pair/cell design is now frozen in `HA-K3-PAIR-1` using the
doubled Cantor polynomial and a successor cell tag. This does not close the
list layer: variable-length tail iteration still needs an independently
selected computation-history representation. Pairing alone yields only a
fixed-length formula schema.

## Repository anchors

- `research/arithmetic-library/ha-number-theory-campaign.json`
- `research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md`
- `research/arithmetic-library/ha-canonical-gcd-lcm-rfc-v1.md`
- `research/arithmetic-library/ha-canonical-pair-cell-rfc-v1.md`
- `PLAN/12_ha_number_theory_campaign.md`
- `book/arithmetic-library/strict-ha-campaign.md`

## Related notes

- [[arithmetic-library-moc]]
- [[peano-lab]]
- [[proof-certificate]]
- [[intuitionistic-logic]]

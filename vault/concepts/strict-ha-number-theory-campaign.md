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

The current registry has 432 theorems. Nine strict-HA tranche-01 interfaces,
16 K4 gcd/LCM interfaces, and 23 M5 generalized-CRT interfaces are public. The
campaign evidence records 95 public references, 121 isolated candidates, and
169 exact receipts across 27 candidate modules and 36 focused test paths. Its
strict-K3 component has 96 rows across 21 modules: 74 signed representation,
normalization, arithmetic, natural-scale, and Bezout-bridge rows, plus 22 pair
constructor, shell, injectivity, functionality, and strict-descent rows. The K4
remainder consists of three canonical-gcd package rows, one signed-gcd client,
five canonical-gcd edge rows, and ten relational-LCM convenience rows. The
definition freeze remains 45 API rows over 44 distinct public theorems, there
are 95 public references, and the catalog has 433 entries: 23
`checked_existing`, 409 `checked_m20`, and one `blocked_by_language`.

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
  subgraph K3P[Strict K3 pair/cell API — 22 rows]
    PC[D01/D02 constructors and validity] --> PS[doubled-triangular shell bounds]
    PS --> PI[D01 component injectivity]
    PC --> PN[D05/D06 nil-cell boundary]
    PI --> CF[D06 joint/head/tail functionality]
    PS --> CB[D01 bounds and D06 strict descent]
  end
  subgraph K4[K4 gcd and LCM clients]
    D --> RG
    RG[public relational gcd + balanced Bezout] --> CG[canonical gcd package — private]
    CG --> GE[canonical gcd edge laws — 5 private rows]
    RG --> SG[K4 signed gcd and Bezout client — private]
    SB --> SG
    RL[IsLCM: 7 public core + 10 private convenience rows] --> BF[A–E public algebraic bridge]
    RG --> BF
    BF --> CE[F public compatible gcd/LCM existence]
    CE --> LT[G public relational LCM totality]
    LT --> LU[H public unique LCM value]
    CE --> GP[I public gcd–LCM product]
    LU --> GP
  end
  GP --> GC[generalized CRT congruence and necessity]
  GC --> GS[all-modulus solvability iff gcd compatibility — public]
  GS --> CL[solution class modulo relational LCM — public]
  CL --> CB[zero/nonzero canonical boundary — public]
  GS --> ED[solution or obstruction + raw-input gcd — public]
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

The canonical gcd/LCM checkpoint is now selectively admitted. The five-row
[`canonical-gcd edge tranche`](../../peano-lab/py/peano_lab/library/ha_canonical_gcd_edges_candidate.py)
pins zero, one, and swap functionality and remains private. The 17-row
[`relational-LCM tranche`](../../peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py)
implements the universal property, projections, leastness, uniqueness,
divisibility, product-bound, self/one, and forced-zero laws. Its literal-safe
expander accepts exactly identifiers and the reviewed literals `0` and `1`;
zero-left is derived from the direct zero-right theorem by symmetry. Exactly
the seven universal rows L01--L07 are public; L08 and C01--C09 remain private.

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

All nine bridge rows A--I are public with their original receipts. The
compatible-pair certificate has 9,038 nodes at depth 60; the final
`gcd_lcm_product` certificate has 10,441 nodes at depth 61. Both zero and
nonzero branches are mutation-audited, every bridge certificate has zero
`DNE` nodes, and public replay preserves every frozen proof-DAG digest. At the
K4 admission checkpoint the registry/catalog counts were 409/410, with 386
catalog rows at `checked_m20`.
The exact private K4 remainder is 19 rows: three canonical-gcd package rows,
five edge rows, ten LCM convenience rows, and the signed-gcd client.

The generalized-CRT campaign is now selectively public. The admitted tranche
is the exact 23-row candidate-factory closure of
`generalized_binary_crt_solvable_iff`,
`generalized_binary_crt_canonical_boundary`, and
`generalized_binary_crt_total_decision`; it occupies runtime indices 409--431.
This closure contains the constructive all-modulus compatibility criterion,
the complete solution class modulo relational LCM, exact uniqueness at zero
LCM, a unique bounded representative at nonzero LCM, compatibility decision,
the supplied-gcd solution-or-obstruction theorem, and the raw-input endpoint
that constructs an existential relational gcd. The public-admission gate pins
the isolated factories, statements, append order, two cold intuitionistic
receipts, resource limits, and false endpoint mutations.

Exactly six reviewed support or convenience rows remain private:
`mod_eq_add_cancel_left`, `mod_eq_add_cancel_right`,
`mod_eq_unscale_nonzero`, `factor_nonzero_right`,
`is_gcd_nonzero_coprime_quotients`, and
`generalized_binary_crt_solvable_iff_nonzero`. The runtime/catalog boundary is
now 432/433. The generated public snapshot has 1,982,360 structural nodes,
468,010 proof objects, 57,692 structural Cut occurrences, 373 Cut-bearing
theorems, 1,185 dependency edges, and ordered root
`4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
The synchronized vault has 432 theorem notes, 531 total notes, and 5,377
resolved links.

The preceding M5 admission gate passed 30 structural and 220 proof/admission
tests, and all 25 browser/deployment contracts passed. After adding the five
private K3 pair/cell modules, the regenerated 185-source local browser app is
sealed as `a-0d9a06f601cf` (`BUILD=2026-08-04k`); no deployment is claimed.

The warning-free 47-source Book rebuild passes 26 source/explorer tests and
integrity over 2,325 HTML pages. Its byte-identical source/built explorer trees
contain 2,285 files; the 2,493-file HTML tree has SHA-256
`d9eddd01a0dcc228ceb17b75c8595f743c7e2b6bdcb1ba44e9c260e98b33f558`.

The independent pair/cell design is frozen in `HA-K3-PAIR-1` using the
doubled Cantor polynomial and a successor cell tag. Its 22-row private API now
closes literal constructors, fixed-component output functionality, constructor
validity, shell bounds and separation, doubled-offset cancellation, exact D01
component injectivity, the nil/constructed-cell boundary, D06 joint/head/tail
functionality, D01 component bounds, and strict D06 head/tail descent. It has
not been publicly admitted and does not decide arbitrary valid codes. It also
does not close the list layer: variable-length tail iteration still needs an
independently selected computation-history representation. Pairing alone
yields only a fixed-length formula schema; uniform lists and maps remain open.

## K3B reverse-history closure checkpoint

[`HA-K3B-CELLHISTORY-1`](../../research/arithmetic-library/ha-cell-history-rfc-v1.md)
freezes post-K4/M3 reverse `CellHistory` and existential `CellListLen`
definitions. WMI job `219203` checked all eight first-ten theorem rows twice
from the empty context. Exact receipts in order
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` are:

- `cell_history_nil = (155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)`;
- `cell_history_extend = (29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)`;
- `cell_history_succ_elim = (1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)`;
- `cell_list_zero_iff_nil = (1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)`;
- `cell_list_succ_iff_cell = (30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)`;
- `cell_list_length_functional = (34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)`;
- `cell_list_length_le_code = (31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)`;
- `cell_list_length_total = (29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)`.

All eight rows have zero DNE and status `closed_checked_candidate`. The
authoritative [closure report](../../artifacts/peano-library/ha-k3b-cell-history-closure-219203.json)
has SHA-256
`6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`;
job `219203` completed `0:0` on `c3n1` in `00:04:46` with
`MaxRSS=82428K`. Gates G1--G6 and G7's quarantine/closure portion pass, but
public admission was deliberately not performed. The rows remain private,
unregistered, and unadmitted. Consequently strict K3 remains 96 rows across
21 modules and the unchanged campaign JSON remains 95 public references, 121
private candidates, and 169 receipts. The light local audit is
`make ha-k3b-cell-history-check`, separate from the heavy campaign target.

## K3B ListAt design checkpoint

[`HA-K3B-LISTAT-1`](../../research/arithmetic-library/ha-cell-list-lookup-rfc-v1.md)
freezes only the canonical lookup surface and its proof dependency order.
Outer-head index `i` selects construction edge `j` through
`j + S i = l`; existential witnesses are ordered `l b c j t u`. The full PA
expansion has 3,331 characters, 54 formula constructors, 210 AST nodes, and
SHA-256
`b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce`.
Seven focused checks pass. The prerequisite
`cell_history_extend_preserves_prefix` now has a dependency-curried checked
body receipt `(5,99,139,37,139,138,0)` and four focused audits. WMI job
`219209` closed it twice at
`(29369,81,4668,4896,229,241,7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498)`;
the [report](../../artifacts/peano-library/ha-k3b-listat-prefix-closure-219209.json)
has SHA-256
`0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560`.
The theorem exposes the pointwise beta-prefix map hidden by the current
existential extension contract, but remains private and unadmitted. No lookup
equation or admission is claimed. The light gate is
`make ha-k3b-list-lookup-check`.

## Repository anchors

- `research/arithmetic-library/ha-number-theory-campaign.json`
- `research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md`
- `research/arithmetic-library/ha-canonical-gcd-lcm-rfc-v1.md`
- `research/arithmetic-library/ha-generalized-crt-rfc-v1.md`
- `research/arithmetic-library/ha-canonical-pair-cell-rfc-v1.md`
- `research/arithmetic-library/ha-cell-history-rfc-v1.md`
- `research/arithmetic-library/ha-cell-list-lookup-rfc-v1.md`
- `PLAN/12_ha_number_theory_campaign.md`
- `book/arithmetic-library/strict-ha-campaign.md`

## Related notes

- [[arithmetic-library-moc]]
- [[peano-lab]]
- [[proof-certificate]]
- [[intuitionistic-logic]]

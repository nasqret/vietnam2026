# Bertrand's postulate campaign

This campaign aims to prove Bertrand's postulate completely inside the
unchanged intuitionistic arithmetic kernel. Its primary endpoint is

$$
\forall n\ne0\;\exists p\,
\bigl(\operatorname{Prime}(p)\land n<p\land p\le 2n\bigr),
$$

followed by the traditional strict corollary for $1<n$:

$$
\exists p\,
\bigl(\operatorname{Prime}(p)\land n<p<2n\bigr).
$$

```{admonition} Current Alpha-v19 evidence and historical enrollment boundary
:class: important
Bertrand's postulate is **fully proved and admitted for independently checked
Alpha use**. Historical immutable Alpha v18 first binds the exact
**544-node, 1,917-edge**
self-contained constructive proof bundle for `bertrand_strict`; every node in
its complete dependency closure is checked by the original intuitionistic
kernel and the independently compiled Lean verifier. Conservative proof-body
sharing additionally produces an original-kernel-accepted ordinary
empty-context strict-root certificate of 201,285 structural nodes and only
45,254 distinct proof objects, below every unchanged replay limit. Both
`bertrand_closed_upper` and `bertrand_strict` have actual `alpha_closed`
checked-use authority. Stable remains the unchanged 432-theorem default.

The Alpha-v12 numbers, body-only labels, and tranche receipts below are
**historical first-enrollment checkpoints**. That sealed release preserved its
1,123-row Alpha-v11 parent and appended the final 180 reviewed proof bodies in
nine twenty-row microbatches without granting checked use. Historical Alpha
v18 later closes every exact strict-root ancestor while retaining 67 auxiliary
Bertrand rows outside that dependency slice as `body_checked`. Current Alpha
v19 independently closes all 67 auxiliary rows as well: the entire historical
Bertrand development now has checked-use authority, without Stable promotion.
```

The binding statement, logic, validation, and release rules are frozen in
[`RFC HA-R6-BERTRAND-1`](https://github.com/nasqret/vietnam2026/blob/9efc5cd95ae7698a092c922d83e29f9d2dedea24/research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md).
Its threshold representation is amended by
[`RFC HA-R6-BERTRAND-2`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v2.md):
the mathematical cutoff 512 has canonical native carrier `16 * 32`, public
Bertrand surfaces retain `n + n`, and any move to an internal `2 * n` helper
requires a live checked equality rewrite. The amendment changes no endpoint,
logical authority, or evidence status.
The additive Choose/central-binomial tranche is separately bound by
[`RFC HA-R6-BERTRAND-CB-1`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-choose-central-binomial-tranche-rfc-v1.md).
The Alpha-v9 Primorial append is bound per source by the
[`foundation RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-foundation-tranche-rfc-v1.md)
and
[`membership RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-membership-tranche-rfc-v1.md).
The Alpha-v10 split append is bound by the
[`interval-split RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-primorial-interval-split-tranche-rfc-v1.md).
The Alpha-v11 append is bound by the duplicate-free, Primorial/Choose interval,
central-binomial upper, Primorial-four-power, and central-prime-support RFCs.
The Alpha-v12 append is bound by the B6 release RFC and the seventeen B5, B7,
B8, BP01, and BP02 tranche RFCs in the same research directory.
It selects an integer-only Erdős--Tochiori central-binomial proof. No real
numbers, logarithms, primitive binomial operation, classical axiom, or new
kernel rule is permitted.

<p>
  <a class="btn btn-primary"
     href="../_static/bertrand-proof-explorer/graph.html?target=BT0127&amp;view=prerequisites&amp;edges=focus">
    Open the complete interactive Bertrand proof map
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/tag/BT0127.html">
    Read the final strict theorem · BT0127
  </a>
</p>

The {doc}`complete Bertrand proof explorer <bertrand-proof-explorer>` contains
all 544 theorem nodes and 1,917 direct edges in the transitive closure of
`bertrand_strict`.

## Why the proof remains constructive

The finite interval is decided before the contradiction argument begins:

```text
bounded_prime_interval_search(l,u)
  |
  |-- witness p with Prime(p), l<p, p<=u  ---> return p
  `-- pointwise certificate excluding every such p
                                                |
                                                `-- refute by integer bounds
                                                    and use false.elim
```

Consequently, the negative branch is explicit data. The proof never turns
$\neg\neg\exists p$ into $\exists p$.

## Current Alpha v12 layer (historical first-enrollment checkpoint)

Alpha v12 is an additive child of the sealed 1,123-row Alpha v11 ledger. Alpha
v8 remains the sealed Choose/central-binomial parent, v9 the sealed Primorial
foundation and membership parent, v10 the sealed interval-split parent, and
v11 the sealed B4-capstone/B5-support parent.

| Quantity | Exact value |
|---|---:|
| Alpha v12 specifications | 1,303 |
| Stable rows | 432 |
| Alpha-only rows | 871 |
| checked-use rows | 570 |
| direct dependency edges | 4,302 |
| dependency layers | 45 |
| first-round Bertrand rows | 21 |
| Round-2 Bertrand rows | 42 |
| `FactorialVal` rows | 7 |
| Alpha-v6 threshold / finite-sum / power / valuation rows | 8 + 5 + 5 + 3 |
| Alpha-v7 constructor / successor / total-power / base / recurrence / transport / equality rows | 3 + 5 + 4 + 2 + 5 + 3 + 2 |
| Alpha-v8 Choose / central baseline and recurrence / bridge / lower-bound rows | 24 + 14 |
| Alpha-v9 Primorial foundation / membership and monotonicity rows | 10 + 11 |
| Alpha-v10 Product split / Primorial interval rows | 1 + 8 |
| Alpha-v11 duplicate-free / Choose interval / central upper / B4 / B5-support rows | 10 + 10 + 6 + 7 + 5 |
| Alpha-v12 B6 support plus B5--BP02 completion rows | 43 + 137 |

At the sealed Alpha-v12 checkpoint, all 401 campaign additions were
`body_checked` and checked use remained unchanged at 570. Its historical
enrollment root is
`f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b`.
The full edition identity is
`bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061`.
The ordered-specification, membership, evidence, and channel-pointer roots are
`362da94c3c5e788f296f315b86b5d63534c1567ce00911dbb27227a66ab50e28`,
`726c6134461dace943f909a0073ca0a6cae95a54ff306f8aeefeb3d9a5151926`,
`de8a6a57b828c2b3893c6fb31f2611d5180f8de4d1002a21a681739616b761b5`,
and
`7ad0c942a2239532696f5d99ee1dc985e13302cf73b4637497b879871d05752c`.
The deterministic historical channel pointer is
`artifacts/peano-library/channels-v12.json`; its catalog, metrics, and reduced
graph are the matching `catalog-v12.json`, `metrics-v12.json`, and
`dependency-graph-v12.mmd`.
Their catalog, metrics, reduced-graph, and channel-pointer SHA-256 values are
`825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109`,
`64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4`,
`583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8`,
and
`0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982`.
The sealed v7 catalog, metrics, reduced graph, and
channels SHA-256 values remain
`7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4`,
`c40f18bda0ec8feb9294cf445d08b51daf868e46b3931daf55bad91413d39e0d`,
`85a53bd719e227a31d5cff15fc25ff66abaa82d498030f5a918a7c40271abc9e`,
and
`fe9c11ec8a622eb759053a42ee6acb7c2bcb1d454fe0dc5fa4b729a07ffbbd30`.
The v12 evidence partition is exactly 432 `stable_closed`, 138 `alpha_closed`,
732 `body_checked`, and one `pending_layered_closure` row. No v12 row was
promoted.

### B0 — constructive interval search

- `prime_strictly_above_decidable`;
- `bounded_prime_interval_search`;
- `prime_interval_exclusion_refutes_witness`;
- `bounded_prime_interval_decidable`.

The interval orientation is exactly $(l,u]$. The largest local closed
certificate in this group has 2,896 structural nodes and depth 78.

### B1 — quantitative powers and order

- `mul_le_mul`;
- `le_mul_of_one_le_right` and `le_mul_of_one_le_left`;
- `pow_base_monotone`;
- `one_le_pow`;
- `pow_nonzero_of_one_le`;
- `pow_exponent_monotone`.

The largest local closure is `pow_exponent_monotone`, at 70,898 nodes and
depth 89.

### B2 — bounded prime-power valuation

- `power_divides_decidable` and `power_divides_zero`;
- `bounded_power_valuation_search` and
  `bounded_power_valuation_exists`;
- `power_valuation_exists` and `power_valuation_functional`;
- the divisibility and maximality projections;
- `prime_power_valuation_exists` and
  `prime_power_valuation_functional`.

The relation chooses the greatest $e\le a$ for which $p^e$ divides $a$.
The prime/nonzero wrapper excludes the intentionally degenerate $p=0,1$ and
$a=0$ cases. The largest local closure is 125,485 nodes and depth 93.

Round 2 adds exponent antitonicity, exact cofactor extraction, prime
nondivisibility across products, and the native theorem

$$
v_p(ab)=v_p(a)+v_p(b)
\qquad(p\text{ prime},\ a,b\ne0).
$$

The complete multiplication certificate has 297,211 nodes, depth 98, and
zero `DNE`; every one of its 39 direct Cuts is independently corrupted and
rejected by the focused gate.

Every direct dependency has a removal or Cut-mutation test, every displayed
statement has an exact hash, and complete proof traversals find zero `DNE`.
At the historical enrollment checkpoint these local closures established
feasibility while their Alpha evidence remained body-only. Exact strict-root
ancestors first acquired independently verified checked-use authority in
historical Alpha v18; current Alpha v19 additionally closes every remaining
auxiliary row.

### Factorial valuations (part of binding gate B2)

Sealed Alpha v5 enrolls seven rows at indices 965--971:

- `factorial_nonzero`;
- `prime_power_valuation_one_zero`;
- `factorial_valuation_exists` and `factorial_valuation_functional`;
- `prime_factorial_valuation_zero`;
- `prime_factorial_valuation_succ`; and
- `prime_factorial_valuation_succ_invert`.

The expanded `FactorialVal(p,n,e)` surface asserts that some $F$ is the
factorial of $n$ and has selected $p$-valuation $e$. The successor theorem is
the exact recurrence

$$
v_p((n+1)!)=v_p(n!)+v_p(n+1),
$$

stated entirely through relational factorial, power, divisibility, and
valuation formulas. Its inverse recovers the valuation of the new factor from
valuations of the two successive factorials. The largest local recursive
closure has 432,090 nodes at depth 105 and zero `DNE`. This is feasibility and
mutation evidence, not an empty-context Alpha admission: every one of the
seven rows has `checked_use=false`, a null proof tag, and null closure metadata.

## Round-2 integer infrastructure

The following tranches are enrolled in Alpha v4 with body-only evidence.

The valuation bridge proves, under `Prime(p)` and $a\ne0$, that the selected
canonical exponent satisfies

$$
p^e\mid a\quad\text{and}\quad p^{e+1}\nmid a.
$$

Its capstone `power_valuation_selected_and_successor_not_divides` closes at
7,632 nodes and depth 75. Exact multiplication is supplied by the later
Round-2 valuation tranche described above.

The integer-envelope spike proves five reusable facts, culminating in

$$
(s+7)^{12}\le4^{s+5}
\Longrightarrow
(s+13)^{12}\le4^{s+11}.
$$

That guard closes at 213,731 nodes and depth 100. It validates the key
six-step mechanism but is not the complete B6 inequality.

The ceiling/square layer proves totality and uniqueness of
$\lceil x/6\rceil$, the exact shift

$$
\left\lceil\frac{(s+6)^2}{6}\right\rceil
=\left\lceil\frac{s^2}{6}\right\rceil+2s+6,
$$

and constructive totality, uniqueness, and monotonicity of
$\lfloor\sqrt{x}\rfloor$. The quotient-budget bridge then derives from
$2n=3q+r$ the witnesses

$$
q+c=n,\qquad 2n\le6c,\qquad
\left\lceil\frac{s^2}{6}\right\rceil\le c,
\qquad q+\left\lceil\frac{s^2}{6}\right\rceil\le n.
$$

Its largest closure is 2,906 nodes. These facts remove the floor/ceiling
representation risk; the remaining B6 risk is the exponential envelope.

## Alpha v6 threshold, finite-sum, and bridge layer

Alpha v6 enrolls the following twenty-one rows, in dependency-topological
source order, over the byte-identical 972-row v5 prefix.

The eight-row threshold tranche proves the numeral bounds used by the
$n\ge2048$ split, transports $64^2\le2n$ through `FloorSqrt`, derives
$42(s+1)\le s^2$ and $7(s+1)\le\lceil s^2/6\rceil$ for $s\ge64$, and packages
the linear residue-window bounds for $64\le s\le69$. Its largest local closure
has 2,352 nodes. It was authored in commit `f35b8ed` and occupies v6 indices
972--979.

The five-row finite Legendre-sum interface supplies
`prime_power_quotient_prefix_exists`, `power_quotient_prefix_transport`,
`prime_legendre_sum_exists`, `legendre_sum_functional`, and
`legendre_sum_zero`. A Gödel-β prefix stores the quotients
$\lfloor n/p^i\rfloor$, and the existing finite-sum relation accumulates them.
The largest local closure has 124,078 nodes. This interface was pushed in
commit `4df44c9`, occupies indices 980--984, and does **not** yet prove
Legendre's equality

$$
v_p(n!)=\sum_{i\ge1}\left\lfloor\frac{n}{p^i}\right\rfloor.
$$

The five-row relational-power bridge at indices 985--989 supplies
`pow_successor_compose`, exact $2^2$ and $2^7$ witnesses, the bridge
$128^{12}=4^{42}$, and `bertrand_guard_base_residue`. The three valuation
bridge rows at indices 990--992 show that the encoded quotient tail vanishes
and connect prime-power divisibility bounds in both directions to the selected
valuation exponent. They were authored in commits `bb24543` and `2f41a97`.

All twenty-one rows were published in Alpha v6 by `5b189f0`. Their exact
dependency-curried bodies replay in the intuitionistic kernel and mutations
fail closed. In the historical Alpha-v6 release, each had evidence
`body_checked`, `checked_use=false`, a null proof tag, and null empty-context
closure metadata. Those local closure measurements were then feasibility
evidence, not empty-context admission; exact strict-root ancestors first
closed in historical Alpha v18 and remain independently checked in current
Alpha v19.

## Alpha v7 recurrence, equality, and $H/J$ layer

Alpha v7 enrolls twenty-four rows over the byte-identical v6 prefix. The first
three are optimized constructive initial-segment constructors:
`eisenstein_initial_segment_indicator_choice`,
`eisenstein_initial_segment_prefix_extend`, and
`eisenstein_initial_segment_prefix_exists`.

The next five are the Legendre-successor ingredients originally authored in
`5b9433a`:

- `division_remainder_successor_cases`;
- `division_successor_quotient_by_bit`;
- `valuation_threshold_bit_decides_power_divides`;
- `power_quotient_prefix_decoded_divrem`; and
- `power_quotient_successor_pointwise_add`.

They feed five finite-recurrence rows culminating in
`prime_legendre_sum_succ`, authored in `de58034`. The recurrence is complete
as dependency-curried body evidence.

The four capacity-shared `PowTotal` rows originally authored in `b2035ce` are
`pow_successor_compose_from_total`, `pow_mul_exp_from_total`,
`pow_exponent_monotone_from_total`, and `pow_two_seed_bundle_from_total`.
They support the two-row compact base-window layer in `70c5b16` and the
three-row compact six-step transport in `985a773`. The final transport theorem
is `bertrand_hj_six_step_from_total`.

Finally, `158d87c` proves `factorial_legendre_successor_agreement` and
`prime_factorial_valuation_eq_legendre_sum`, completing Legendre's equality
with `FactorialVal` at the body-evidence level. `00e8361` supplies the
optimized constructor source needed by the frozen dependency order. All seven
source blocks replay, reject their prescribed mutations, contain zero `DNE`,
and remain fail-closed `body_checked` rows. At that Alpha-v7 checkpoint this
was enrollment, not promotion, and Bertrand's postulate was still open.

## Alpha v8 recurrence-defined Choose and central lower bound

Alpha v8 preserves that complete v7 prefix and appends 38 reviewed rows in two
dependency-topological microbatches. The first 24 construct finite Pascal rows
with Gödel-$\beta$ codes, prove their pointwise and table extensionality, and
derive relational `Choose` existence, functionality, zero, self, Pascal,
symmetry, and positivity laws together with baseline `CentralBinom` wrappers.
The second 14 add the central zero and successor laws, weighted vertical and
factorial bridges, strict arithmetic growth, the exact fourth-row seed, and

$$
4^n<n\binom{2n}{n}\qquad(4\le n).
$$

The exact endpoint is the relational theorem
`four_pow_lt_mul_central_binom`. The tranche is controlled by
[`RFC HA-R6-BERTRAND-CB-1`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-bertrand-choose-central-binomial-tranche-rfc-v1.md),
whose frozen SHA-256 is
`4f337990babf85ffaacdc990f0e09a3c1943b8edb20c72ffef675cbb28cde83b`.
All 38 dependency-curried body receipts replay with combined root
`fb6e40f2470a9c436f02676ea15b99a389ee7495b4c6cd81212a42a7010b4466`.
This is still body evidence: every new row rejects checked replay, and no
Stable promotion or full campaign theorem follows from enrollment alone.

## Alpha v9 Primorial foundation and membership

Alpha v9 preserves the complete v8 prefix and appends 21 reviewed rows in two
dependency-topological microbatches. The first ten freeze the selector and
factor-prefix encodings and the inclusive mathematical Primorial
`Primorial(m,z)`, then prove factor choice and prefix totality, Primorial
existence and functionality, the zero law, successor decomposition, and
positivity. The next eleven prove

$$
\operatorname{Prime}(p)\Longrightarrow
\bigl(p\mid m\#\iff p\le m\bigr),
$$

successor and arbitrary-index divisibility, positive quotients, and weak
numeric monotonicity. The two binding RFCs have SHA-256 values
`c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89`
and
`4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5`.
All 21 dependency-curried body receipts replay with combined root
`1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab`.
This remains body evidence: every new row rejects checked replay, and interval
splitting, duplicate-free external-product comparison, and the final
Primorial bound remain future B4 work.

## Alpha v10 Primorial interval splitting

Alpha v10 preserves the complete v9 prefix and appends nine reviewed rows in
exact 1+8 dependency order. The first row pins only
`beta_product_prefix_suffix_split` from its two-row provider; the unreviewed
concat converse remains excluded. The remaining rows define offset selector
prefixes and interval Primorial products, prove their totality,
functionality, entry transport and shift, restrict a full selector prefix,
and conclude

$$
\operatorname{Primorial}(a+l,z)\Longrightarrow
\exists x,y\,
\bigl(\operatorname{Primorial}(a,x)\land
\operatorname{PrimorialInterval}(a,l,y)\land z=xy\bigr).
$$

The binding RFC has SHA-256
`db7d2d58f0b44d3793673b21496ea7f5d5d2747c75795587f6b1c99b2e80f46e`.
All nine dependency-curried bodies replay with combined root
`fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c`.
This remains body evidence: every new row rejects checked replay, and
duplicate-free external-product comparison and the final Primorial bound
remain future B4 work.

## Alpha v11 B4 capstone and B5 prime support

Alpha v11 preserves the complete v10 prefix and appends thirty-eight reviewed
rows in exact 20+18 microbatches. The first microbatch proves duplicate-free
prime-product comparison and connects Primorial intervals to factorial and
Choose divisibility. The second supplies cap-safe central-binomial upper laws,
proves the public bound

$$
\operatorname{Primorial}(n,z)\land \operatorname{Pow}(4,n,q)
\Longrightarrow z\le q,
$$

and adds the first B5 prime-divisor and valuation-support rows. In particular,
under an explicit no-Bertrand certificate, every prime divisor of the central
binomial coefficient is constructively confined to the three live ranges used
by the eventual five-range factorization.

At the historical Alpha-v11 checkpoint, all thirty-eight rows carried body
evidence only. Their source blocks bind to
five subordinate RFCs and retain exact focused empty-context receipts, but
that historical Alpha enrollment itself granted no checked use and changed no
Stable row. Exact strict-root ancestors were independently promoted later in
historical Alpha v18; current Alpha v19 closes the remaining auxiliary rows.

## Alpha v12 complete Bertrand proof

Alpha v12 appends the complete dependency-closed proof chain in nine exact
twenty-row microbatches. The first forty-three rows publish the reviewed B6
base-window, all-root, growth, main-inequality, and finite-product-order
support. The remaining 137 rows complete B5's five-range factorization, derive
the B7 large-input contradiction, certify and cover the B8 finite range, and
close both public endpoints:

```text
bertrand_closed_upper : n != 0 -> exists p, Prime(p) /\ n < p /\ p <= n+n
bertrand_strict       : 1 < n  -> exists p, Prime(p) /\ n < p /\ p <  n+n
```

The focused BP01 and BP02 suites independently rebuild their complete
empty-context graphs and kernel-check the final certificates. Historical Alpha
v12 recorded the same exact source bodies and provenance as `body_checked`
evidence only and intentionally left checked-use and Stable unchanged. The
later complete Alpha-v18 proof bundle independently closes every strict-root
dependency and grants both exact endpoints checked-use authority. Current
Alpha v19 preserves that bundle and independently closes all additional
Bertrand rows; Stable membership remains unchanged.

## Dependency roadmap

```text
checked Alpha baseline
  |-- B0 bounded interval decision
  `-- B1 discrete inequality/fold API
        |-- B2 prime-power valuations and Legendre
        |-- B3 Choose/CentralBinom [Alpha v8 body evidence]
        `-- B4 Primorial [Alpha v11 body evidence; bound closed; depends on B3]

B2 + B3 + B4 --------------------> B5 central factor upper bound [complete]
B1 --------------------------------> B6 native main inequality [complete]
B0 + B3 + B5 + B6 ----------------> B7 n >= 512 [complete]
B0 + B7 + certified prime chain ---> B8 endpoints BP01 and BP02 [complete]
```

The retained Alpha-v8 central lower bound proves $4^n<n\binom{2n}{n}$ at the
body-evidence level. Under an explicit
no-prime certificate for $(n,2n]$, valuations and the primorial will give

$$
\binom{2n}{n}
\le
(2n)^{\lfloor\sqrt{2n}\rfloor}
4^{\lfloor2n/3\rfloor}.
$$

The exact natural-number B6 target is

$$
n(2n)^{\lfloor\sqrt{2n}\rfloor}
4^{\lfloor2n/3\rfloor}\le4^n
\qquad(n\ge512).
$$

The post-v7 candidate work reduces its difficult growth component to six residue
classes using

$$
H(s)=(s+1)^{2s+2},\qquad
E(s)=\left\lceil\frac{s^2}{6}\right\rceil,
$$

and the exact identity $E(s+6)=E(s)+2s+6$. `FloorSqrt`, ceiling-by-six, the
quotient complement, threshold arithmetic, the relational-power bridge,
compact $H/J$ bases, six-step transport, the all-$s$ envelope, and
`bertrand_main_inequality_nat` now have reviewed candidate bodies and closure
receipts. The post-v7 envelope and main-inequality rows remain outside Alpha
v9, however, and cannot feed a checked large-$n$ contradiction until the B4
primorial bound, B5 no-prime central upper bound, and branch integration are
complete.

The implemented candidate lineage uses the RFC-v2 cutoff carrier
`16 * 32`, mathematically 512, and the root-32 envelope over the six bases
$s=32,\ldots,37$. In particular, `bertrand_hj_envelope_thirty_two` supplies
the factorized large-branch envelope without placing a literal 512 in the
public proof surface. The earlier possible $n\ge2048$ optimization and roots
$64,\ldots,69$ were not selected for this lineage.

## Durable checkpoints

| Commit | Content |
|---|---|
| `10dc017` | multiplicative order and base-power monotonicity |
| `6739532` | campaign RFC, constructive interval search, power growth |
| `be5b735` | bounded valuation existence and functionality |
| `941ad70` | selected valuation and successor nondivisibility |
| `3ce8a90` | additive, fail-closed Alpha v3 channel |
| `9efc5cd` | integer-envelope feasibility spike |
| `d6dac45` | ceiling-by-six and floor-square relation layer |
| `3cc6994` | constructive floor-square-root totality and monotonicity |
| `654aab2` / `bdb9cf7` | two-process closure infrastructure and retained Slurm diagnostics |
| `88d9e92` | exact prime-power valuation multiplication |
| `139b6ce` | floor/ceiling quotient budget |
| `e605faa` | additive, fail-closed Alpha v4 channel |
| `05cb3ff` | seven-row recursive `FactorialVal` proof layer |
| `f35b8ed` | eight threshold and residue-window base inequalities |
| `4df44c9` | five-row finite Legendre-sum interface |
| `85625d6` | additive, fail-closed Alpha v5 channel |
| `bb24543` | five-row relational-power bridge |
| `2f41a97` | three-row Legendre-valuation bridge |
| `5b9433a` | five Legendre-successor bodies, later enrolled in v7 |
| `b2035ce` | four capacity-shared `PowTotal` bodies, later enrolled in v7 |
| `5b189f0` | additive, fail-closed Alpha v6 channel |
| `70c5b16` | compact two-row $H/J$ base window |
| `de58034` | five-row finite Legendre recurrence |
| `985a773` | compact three-row $H/J$ six-step transport |
| `158d87c` | factorial valuation equals the finite Legendre sum |
| `00e8361` | optimized constructive initial-segment constructors |
| `874e81e` | additive, fail-closed Alpha v7 channel |
| `d1cbe16` | all-root $H/J$ envelope candidate bodies |
| `8ea03f2` | B6 main-inequality candidate bodies |
| `d1ad971` | dependency-closed B6 inequality graph audit |
| `d46e513`--`74dc219` | frozen 38-row Choose/central-binomial tranche |
| `dfb2673` | frozen ten-row Primorial foundation tranche |
| `b0bc5de` | frozen eleven-row Primorial membership and monotonicity tranche |
| `c45d68a` | frozen Product split and eight-row Primorial interval tranche |
| `5eef9a5`--`7539b44` | dependency-closed B4 comparison, interval, upper, and capstone tranches |
| `56ecb02` | first five B5 central prime-divisor support rows |

All checkpoints are pushed to `nasqret/vietnam2026` on
`agent/new-theorems-tranche-01`.

## Reproduce the current gates

```bash
make peano-library-alpha-v12-check
make book-bertrand-proof-explorer
make book-bertrand-defined-explorer
```

The first command validates the Alpha-v12 evidence boundary, including the
complete 180-row dependency-closed Bertrand suffix. Its expensive body replay
and focused proof suites run in bounded, serial stages so a single Python
process cannot retain the campaign's proof DAGs indefinitely. The second
command deterministically regenerates the 544-node interactive proof map from
the byte-frozen v12 catalog. The third adds the conservative definition-aware
reading edition, with linked campaign notation and the same exact proof
dependencies. Successful replay does not upgrade Alpha evidence or promote
anything to Stable.

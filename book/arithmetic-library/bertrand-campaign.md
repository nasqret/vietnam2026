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

```{admonition} Current evidence boundary
:class: warning
Bertrand's postulate is **not yet proved** in this repository. Alpha v5 is a
sealed 972-row parent, and current Alpha v6 contains ninety-one campaign
specifications whose dependency-curried bodies check. Its twenty-one new rows
enroll eight threshold-base facts, five finite Legendre-sum facts, five
relational-power facts, and three Legendre-valuation bridge facts. They remain
`body_checked`, have no empty-context admission metadata, and are unavailable
through checked theorem replay. Five Legendre-successor rows and four
capacity-shared `PowTotal` rows are pushed candidates outside v6. The finite
Legendre recurrence and its equality with factorial valuation, binomial
coefficients, central-binomial bounds, the primorial bound, exact main
inequality, finite coverage, and both Bertrand endpoints remain open. The
$H/J$ base-window layer is currently in progress.
```

The binding statement, logic, representation, validation, and release rules
are frozen in
[`RFC HA-R6-BERTRAND-1`](https://github.com/nasqret/vietnam2026/blob/9efc5cd95ae7698a092c922d83e29f9d2dedea24/research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md).
It selects an integer-only Erdős--Tochiori central-binomial proof. No real
numbers, logarithms, primitive binomial operation, classical axiom, or new
kernel rule is permitted.

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

## Current Alpha v6 layer

Alpha v6 is an additive child of the sealed 972-row Alpha v5 ledger.

| Quantity | Exact value |
|---|---:|
| Alpha v6 specifications | 993 |
| Stable rows | 432 |
| Alpha-only rows | 561 |
| checked-use rows | 570 |
| direct dependency edges | 2,977 |
| dependency layers | 45 |
| first-round Bertrand rows | 21 |
| Round-2 Bertrand rows | 42 |
| `FactorialVal` rows | 7 |
| Alpha-v6 threshold / finite-sum / power / valuation rows | 8 + 5 + 5 + 3 |

All ninety-one campaign additions are `body_checked`; checked use remains
unchanged at 570. The current enrollment root is
`dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7`.
The ordered specification root is
`50f395c30e4f21a7b7602bc56451bf2363d1a23d811bba62a33c08e2defc1da1`.
The full edition identity is
`7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b`.
The membership, evidence, and channel-pointer roots are respectively
`bd8faa84d1ef0c090fb07aa21ecd966d4f4356999fcd12cf4f74d0e5ae8572b8`,
`c1fcedbd7bbc5e8655dbce3b00ab0bd9296489a3b4358fb548eeb32d081e8682`,
and
`4dc0f9411227e041dbbbcc2626a04d995a6ceeedb91fe9c2d246f377596693b7`.
The deterministic channel pointer is
[`channels-v6.json`](https://github.com/nasqret/vietnam2026/blob/5b189f080ddb21e36e68359bc2aea28b550d5ee2/artifacts/peano-library/channels-v6.json).
The v6 catalog, metrics, reduced graph, and channels SHA-256 values are
`c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d`,
`f2a6c22b9fe50581a4cfe8d3b1b494fa274d26d0b51b60e92735650a09391be7`,
`532c2482a3b1c371026bd80b1b7297faffc4a1b1ee3e53031e499f1611b3ae16`,
and
`6ef8bb93b2e24bdfe45389ca9417b6333ce83ae249ee49a957959a6b3471b86c`.
The exact suffix-depth and fresh body-receipt roots are
`d103de2054a0bd4de3b2faa9d98435a4f705594f8a69968e9ca956c455cb61d3`
and
`c23b2fc58fabd3803a0ded5f02d4ea348d67a00b25f5b28b35f3d6bcb00ff2f1`.

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
These local closures establish feasibility; the Alpha evidence remains
body-only until the versioned two-process cold receipt is accepted.

### B3 — factorial valuations

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
fail closed. Each nevertheless has evidence `body_checked`,
`checked_use=false`, a null proof tag, and null empty-context closure metadata.
The local closure measurements above are feasibility evidence and are not
empty-context admission.

## Pushed candidates beyond Alpha v6

Two later reviewed proof tranches are pushed but deliberately absent from the
v6 enrollment ledger.

Commit `5b9433a` adds five Legendre-successor ingredients:

- `division_remainder_successor_cases`;
- `division_successor_quotient_by_bit`;
- `valuation_threshold_bit_decides_power_divides`;
- `power_quotient_prefix_decoded_divrem`; and
- `power_quotient_successor_pointwise_add`.

Their exact local closure maxima are 81,828 structural nodes, depth 95, 6,931
distinct objects, and 7,226 proof-DAG edges. These pointwise quotient facts do
not yet supply the finite Legendre-sum recurrence or identify that sum with
`FactorialVal`.

Commit `b2035ce` adds four capacity-shared `PowTotal` candidates:
`pow_successor_compose_from_total`, `pow_mul_exp_from_total`,
`pow_exponent_monotone_from_total`, and `pow_two_seed_bundle_from_total`.
Their checked local closures have respectively 5,327, 10,630, 11,062, and
13,336 structural nodes. Against the frozen historical comparison counts they
save exactly 59,836, 59,833, 59,836, and 119,652 nodes; the maximum observed
depth is 143 and the maximum distinct-object count is 3,140. Sharing is a
capacity result, not enrollment or promotion.

The $H/J$ base-window layer is in progress and has no Alpha-v6 rows. The
finite Legendre recurrence, Legendre's equality, and Bertrand's postulate are
still open.

## Dependency roadmap

```text
B0 interval decision ------------------------------------------+
                                                               |
B1 order, powers, FloorSqrt, floor/ceiling arithmetic ----+    |
                                                          |    |
B2 valuations + finite sums -------+                      |    |
                                    |                      |    |
B3 FactorialVal + Legendre equality-+                      |    |
B4 Choose/CentralBinom -------------+----> B5 factor ranges|    |
              |                     |    + primorial bound |    |
              `---------------------+                      |    |
                                                          v    v
                                                   B6 main inequality
                                                          |
                                          B7 n >= 512 theorem
                                                          |
                                      B8 finite coverage + BP01/BP02
```

The central lower bound will prove $4^n<n\binom{2n}{n}$. Under an explicit
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

The current work reduces its difficult growth component to six residue
classes using

$$
H(s)=(s+1)^{2s+2},\qquad
E(s)=\left\lceil\frac{s^2}{6}\right\rceil,
$$

and the exact identity $E(s+6)=E(s)+2s+6$. `FloorSqrt`, ceiling-by-six, the
quotient complement, threshold arithmetic, and the first relational-power
bridge are now formalized and enrolled body-only. The actual exponential
$H/J$ bases, $H$ transport, and the final power-product bridge remain
obligations; authoring of the base-window layer is in progress.

The first implementation may use the more proof-friendly large branch
$n\ge2048$ rather than 512. Its base roots are $s=64,\ldots,69$, where
$s+1\le128=2^7$ gives uniform relational-power bounds without enormous
evaluated numerals. The finite branch then extends the Landau chain by the
primes 1031 and 2053. This changes only the internal split, not Bertrand's
statement.

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
| `5b9433a` | five Legendre-successor candidates outside v6 |
| `b2035ce` | four capacity-shared `PowTotal` candidates outside v6 |
| `5b189f0` | additive, fail-closed Alpha v6 channel |

All checkpoints are pushed to `nasqret/vietnam2026` on
`agent/new-theorems-tranche-01`.

## Reproduce the current gates

```bash
make peano-library-alpha-v6-check

PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_bertrand_prime_interval_candidate.py \
  peano-lab/py/tests/test_bertrand_power_order_candidate.py \
  peano-lab/py/tests/test_bertrand_power_growth_candidate.py \
  peano-lab/py/tests/test_bertrand_power_valuation_candidate.py \
  peano-lab/py/tests/test_bertrand_power_valuation_laws_candidate.py \
  peano-lab/py/tests/test_bertrand_power_divisibility_candidate.py \
  peano-lab/py/tests/test_bertrand_integer_envelope_candidate.py \
  peano-lab/py/tests/test_bertrand_ceil_sqrt_candidate.py \
  peano-lab/py/tests/test_bertrand_floor_sqrt_total_candidate.py \
  peano-lab/py/tests/test_bertrand_quotient_budget_candidate.py \
  peano-lab/py/tests/test_bertrand_factorial_valuation_candidate.py \
  peano-lab/py/tests/test_bertrand_threshold_base_candidate.py \
  peano-lab/py/tests/test_bertrand_legendre_sum_candidate.py \
  peano-lab/py/tests/test_bertrand_power_bridge_candidate.py \
  peano-lab/py/tests/test_bertrand_legendre_valuation_bridge_candidate.py \
  peano-lab/py/tests/test_bertrand_legendre_successor_candidate.py \
  peano-lab/py/tests/test_bertrand_power_total_candidate.py
```

The first command validates the published Alpha-v6 evidence boundary and
independently replays its twenty-one new dependency-curried bodies. The second
includes expensive local empty-context feasibility checks, including the nine
candidate rows outside v6; it does not upgrade Alpha evidence or promote
anything to Stable.

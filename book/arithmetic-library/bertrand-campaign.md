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
Bertrand's postulate is **not yet proved** in this repository. Alpha v4 is now
a sealed parent, and current Alpha v5 contains seventy campaign specifications
whose dependency-curried bodies check. The seven new rows give the
`FactorialVal` graph, functionality, zero case, successor recurrence, and
successor inversion. They remain `body_checked` and unavailable through
checked theorem replay. A five-row finite Legendre-sum interface and an
eight-row threshold-base tranche are pushed candidates outside v5. The
equality between factorial valuation and that finite sum, binomial
coefficients, central-binomial bounds, the primorial bound, exact main
inequality, finite coverage, and both Bertrand endpoints remain open.
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

## Current Alpha v5 layer

Alpha v5 is an additive child of the sealed 965-row Alpha v4 ledger.

| Quantity | Exact value |
|---|---:|
| Alpha v5 specifications | 972 |
| Stable rows | 432 |
| Alpha-only rows | 540 |
| checked-use rows | 570 |
| direct dependency edges | 2,912 |
| dependency layers | 45 |
| first-round Bertrand rows | 21 |
| Round-2 Bertrand rows | 42 |
| `FactorialVal` rows | 7 |

All seventy campaign additions are `body_checked`; checked use remains
unchanged at 570. The current enrollment root is
`46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473`.
The full edition identity is
`bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af`.
The deterministic channel pointer is
[`channels-v5.json`](https://github.com/nasqret/vietnam2026/blob/85625d6ad7a3f7ce4140a5ad2c3ec182d66c0ecd/artifacts/peano-library/channels-v5.json).

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

Alpha v5 enrolls seven rows at indices 965--971:

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

## Pushed candidates beyond Alpha v5

Two reviewed proof tranches are pushed but deliberately absent from the v5
enrollment ledger.

The eight-row threshold tranche proves the numeral bounds used by the
$n\ge2048$ split, transports $64^2\le2n$ through `FloorSqrt`, derives
$42(s+1)\le s^2$ and $7(s+1)\le\lceil s^2/6\rceil$ for $s\ge64$, and packages
the linear residue-window bounds for $64\le s\le69$. Its largest local closure
has 2,352 nodes. It was pushed in commit `f35b8ed`, but it is not an Alpha-v5
row and is not available through edition replay.

The five-row finite Legendre-sum interface supplies
`prime_power_quotient_prefix_exists`, `power_quotient_prefix_transport`,
`prime_legendre_sum_exists`, `legendre_sum_functional`, and
`legendre_sum_zero`. A Gödel-β prefix stores the quotients
$\lfloor n/p^i\rfloor$, and the existing finite-sum relation accumulates them.
The largest local closure has 124,078 nodes. This interface was pushed in
commit `4df44c9`; it does **not** yet prove Legendre's equality

$$
v_p(n!)=\sum_{i\ge1}\left\lfloor\frac{n}{p^i}\right\rfloor.
$$

The separate relational-power bridge that will connect the threshold bounds
to the exponential envelope remains under audit. It is neither enrolled in
Alpha v5 nor claimed as a completed campaign tranche.

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

and the exact identity $E(s+6)=E(s)+2s+6$. `FloorSqrt`, ceiling-by-six, and
the quotient complement are now formalized. The pushed threshold candidate
settles the linear $s=64,\ldots,69$ base-window arithmetic, but the relational
power bridge, the actual exponential $H/J$ bases, $H$ transport, and the final
power-product bridge remain obligations.

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

All checkpoints are pushed to `nasqret/vietnam2026` on
`agent/new-theorems-tranche-01`.

## Reproduce the current gates

```bash
make peano-library-alpha-v5-check

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
  peano-lab/py/tests/test_bertrand_legendre_sum_candidate.py
```

The first command validates the published Alpha-v5 evidence boundary and
replays its seven new dependency-curried bodies. The second includes expensive
local empty-context feasibility checks, including candidates outside v5; it
does not upgrade Alpha evidence or promote anything to Stable.
